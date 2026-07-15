from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .adapters import CostBudget, OpenRouterModelSpec
from .models import GenerationConfig

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
_ERROR_LIMIT = 240
_MAX_PUBLIC_RESPONSE_BYTES = 10 * 1024 * 1024
_COHORT_MODEL_COUNT = 15
_REQUIRED_MODEL_FIELDS = (
    "model_id",
    "canonical_slug",
    "endpoint_tag",
    "provider_name",
    "quantization",
    "request_parameters",
    "reasoning",
    "price_snapshot",
)


class OpenRouterManifestError(ValueError):
    """Raised when pinned cohort metadata does not satisfy schema version 1."""

    def __init__(self, message: str) -> None:
        super().__init__(message[:_ERROR_LIMIT])


class OpenRouterPreflightError(RuntimeError):
    """Raised when public OpenRouter metadata no longer matches the pinned cohort."""

    def __init__(self, message: str) -> None:
        super().__init__(message[:_ERROR_LIMIT])


@dataclass(frozen=True)
class OpenRouterPreflight:
    specs: tuple[OpenRouterModelSpec, ...]
    projected_usd: Decimal
    model_count: int
    calls: int


def _required_mapping(
    value: object, *, label: str, error_type: type[ValueError] | type[RuntimeError]
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise error_type(f"{label} must be an object")
    return value


def _required_list(
    value: object, *, label: str, error_type: type[ValueError] | type[RuntimeError]
) -> list[Any]:
    if not isinstance(value, list):
        raise error_type(f"{label} must be an array")
    return value


def _required_string(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OpenRouterManifestError(f"{label} must be a non-empty string")
    return value


def _positive_decimal(
    value: object, *, label: str, error_type: type[ValueError] | type[RuntimeError]
) -> Decimal:
    if isinstance(value, bool) or isinstance(value, (list, dict)) or value is None:
        raise error_type(f"{label} must be a finite positive decimal")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise error_type(f"{label} must be a finite positive decimal") from None
    if not amount.is_finite() or amount <= 0:
        raise error_type(f"{label} must be a finite positive decimal")
    return amount


def _validate_model_id_for_url(model_id: str, *, label: str) -> None:
    segments = model_id.split("/")
    if len(segments) < 2 or any(segment in {"", ".", ".."} for segment in segments):
        raise OpenRouterManifestError(f"{label} must be a safe routed model ID")


def _manifest_spec(entry: object, index: int) -> OpenRouterModelSpec:
    label = f"models[{index}]"
    model = _required_mapping(entry, label=label, error_type=OpenRouterManifestError)
    missing = [field for field in _REQUIRED_MODEL_FIELDS if field not in model]
    if missing:
        raise OpenRouterManifestError(f"{label} is missing required field {missing[0]}")

    model_id = _required_string(model["model_id"], label=f"{label}.model_id")
    _validate_model_id_for_url(model_id, label=f"{label}.model_id")
    canonical_slug = _required_string(model["canonical_slug"], label=f"{label}.canonical_slug")
    endpoint_tag = _required_string(model["endpoint_tag"], label=f"{label}.endpoint_tag")
    provider_name = _required_string(model["provider_name"], label=f"{label}.provider_name")
    quantization = _required_string(model["quantization"], label=f"{label}.quantization")

    parameters = _required_list(
        model["request_parameters"],
        label=f"{label}.request_parameters",
        error_type=OpenRouterManifestError,
    )
    if not parameters:
        raise OpenRouterManifestError(f"{label}.request_parameters must not be empty")
    normalized_parameters = tuple(
        _required_string(parameter, label=f"{label}.request_parameters") for parameter in parameters
    )
    if len(set(normalized_parameters)) != len(normalized_parameters):
        raise OpenRouterManifestError(f"{label}.request_parameters must be unique")

    reasoning = model["reasoning"]
    if reasoning is not None and not isinstance(reasoning, dict):
        raise OpenRouterManifestError(f"{label}.reasoning must be an object or null")
    if reasoning is not None and "reasoning" not in normalized_parameters:
        raise OpenRouterManifestError(
            f"{label}.request_parameters must include reasoning when configured"
        )
    output_cap_parameters = {"max_tokens", "max_completion_tokens"}.intersection(
        normalized_parameters
    )
    if len(output_cap_parameters) != 1:
        raise OpenRouterManifestError(
            f"{label}.request_parameters must include exactly one output cap parameter"
        )

    price_snapshot = _required_mapping(
        model["price_snapshot"],
        label=f"{label}.price_snapshot",
        error_type=OpenRouterManifestError,
    )
    for field in ("prompt", "completion"):
        if field not in price_snapshot:
            raise OpenRouterManifestError(f"{label}.price_snapshot is missing {field}")
    prompt_price = _positive_decimal(
        price_snapshot["prompt"],
        label=f"{label}.price_snapshot.prompt",
        error_type=OpenRouterManifestError,
    )
    completion_price = _positive_decimal(
        price_snapshot["completion"],
        label=f"{label}.price_snapshot.completion",
        error_type=OpenRouterManifestError,
    )

    return OpenRouterModelSpec(
        model_id=model_id,
        canonical_slug=canonical_slug,
        endpoint_tag=endpoint_tag,
        provider_name=provider_name,
        quantization=quantization,
        supported_parameters=frozenset(normalized_parameters),
        reasoning=reasoning,
        prompt_price=prompt_price,
        completion_price=completion_price,
    )


def load_cohort_manifest(
    path: str | Path, expected_count: int = _COHORT_MODEL_COUNT
) -> tuple[OpenRouterModelSpec, ...]:
    """Load and strictly validate a pinned OpenRouter cohort manifest."""

    if (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count <= 0
    ):
        raise OpenRouterManifestError("expected_count must be a positive integer")
    if expected_count != _COHORT_MODEL_COUNT:
        raise OpenRouterManifestError(
            f"OpenRouter reference cohort must contain exactly {_COHORT_MODEL_COUNT} models"
        )
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OpenRouterManifestError(
            f"unable to load cohort manifest ({type(error).__name__})"
        ) from None

    manifest = _required_mapping(payload, label="manifest", error_type=OpenRouterManifestError)
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise OpenRouterManifestError("manifest.schema_version must equal 1")
    if type(manifest.get("model_count")) is not int:
        raise OpenRouterManifestError("manifest.model_count must be an integer")
    if manifest["model_count"] != expected_count:
        raise OpenRouterManifestError(
            f"manifest.model_count must equal expected count {expected_count}"
        )
    models = _required_list(
        manifest.get("models"), label="manifest.models", error_type=OpenRouterManifestError
    )
    if len(models) != expected_count:
        raise OpenRouterManifestError(
            f"manifest.models must contain exactly {expected_count} entries"
        )

    specs = tuple(_manifest_spec(entry, index) for index, entry in enumerate(models))
    for field in ("model_id", "canonical_slug"):
        values = [getattr(spec, field) for spec in specs]
        if len(set(values)) != len(values):
            raise OpenRouterManifestError(f"manifest {field} values must be unique")
    return specs


def _get_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read(_MAX_PUBLIC_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as error:
        raise OpenRouterPreflightError(f"public metadata GET returned HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise OpenRouterPreflightError(
            f"public metadata GET failed ({type(error).__name__})"
        ) from None
    if len(body) > _MAX_PUBLIC_RESPONSE_BYTES:
        raise OpenRouterPreflightError("public metadata response exceeds size limit")
    try:
        return json.loads(body)
    except (UnicodeError, json.JSONDecodeError):
        raise OpenRouterPreflightError("public metadata response is not valid JSON") from None


def _fetch_public(get_json: Callable[[str], Any], url: str, *, label: str) -> Any:
    try:
        return get_json(url)
    except OpenRouterPreflightError:
        raise
    except Exception as error:
        raise OpenRouterPreflightError(
            f"public metadata GET failed for {label} ({type(error).__name__})"
        ) from None


def _catalogue_entry(catalogue: object, spec: OpenRouterModelSpec) -> Mapping[str, Any]:
    root = _required_mapping(
        catalogue, label="model catalogue", error_type=OpenRouterPreflightError
    )
    entries = _required_list(
        root.get("data"), label="model catalogue.data", error_type=OpenRouterPreflightError
    )
    matches = [
        entry
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("id") == spec.model_id
    ]
    if len(matches) != 1:
        raise OpenRouterPreflightError(
            f"model catalogue must contain exactly one entry for {spec.model_id}"
        )
    entry = matches[0]
    if entry.get("canonical_slug") != spec.canonical_slug:
        raise OpenRouterPreflightError(f"canonical slug drift for {spec.model_id}")
    return entry


def _endpoint_canonical_slug(endpoint: Mapping[str, Any], model_id: str) -> str:
    name = endpoint.get("name")
    if not isinstance(name, str) or " | " not in name:
        raise OpenRouterPreflightError(f"endpoint name is malformed for {model_id}")
    # The endpoint API omits canonical_slug and appends it to the display name.
    canonical_slug = name.rsplit(" | ", 1)[1]
    if not canonical_slug:
        raise OpenRouterPreflightError(f"endpoint canonical slug is missing for {model_id}")
    return canonical_slug


def _live_spec(payload: object, pinned: OpenRouterModelSpec) -> OpenRouterModelSpec:
    root = _required_mapping(
        payload, label="endpoint response", error_type=OpenRouterPreflightError
    )
    data = _required_mapping(
        root.get("data"), label="endpoint response.data", error_type=OpenRouterPreflightError
    )
    if data.get("id") != pinned.model_id:
        raise OpenRouterPreflightError(f"endpoint response model drift for {pinned.model_id}")
    endpoints = _required_list(
        data.get("endpoints"),
        label="endpoint response.data.endpoints",
        error_type=OpenRouterPreflightError,
    )
    matches = [
        endpoint
        for endpoint in endpoints
        if isinstance(endpoint, Mapping)
        and endpoint.get("tag") == pinned.endpoint_tag
        # OpenRouter publishes zero for healthy and negative values for degraded routes.
        and type(endpoint.get("status")) is int
        and endpoint["status"] == 0
    ]
    if len(matches) != 1:
        raise OpenRouterPreflightError(
            f"pinned route must resolve to one healthy endpoint for {pinned.model_id}"
        )
    endpoint = matches[0]
    if endpoint.get("model_id") != pinned.model_id:
        raise OpenRouterPreflightError(f"endpoint model ID drift for {pinned.model_id}")
    if _endpoint_canonical_slug(endpoint, pinned.model_id) != pinned.canonical_slug:
        raise OpenRouterPreflightError(f"endpoint canonical slug drift for {pinned.model_id}")
    if endpoint.get("provider_name") != pinned.provider_name:
        raise OpenRouterPreflightError(f"endpoint provider drift for {pinned.model_id}")
    if endpoint.get("quantization") != pinned.quantization:
        raise OpenRouterPreflightError(f"endpoint quantization drift for {pinned.model_id}")

    supported = endpoint.get("supported_parameters")
    if not isinstance(supported, list) or any(not isinstance(value, str) for value in supported):
        raise OpenRouterPreflightError(
            f"endpoint supported parameters are malformed for {pinned.model_id}"
        )
    required = set(pinned.supported_parameters)
    if pinned.reasoning is not None:
        required.add("reasoning")
    missing = required.difference(supported)
    if missing:
        raise OpenRouterPreflightError(
            f"endpoint is missing required parameters for {pinned.model_id}"
        )

    pricing = _required_mapping(
        endpoint.get("pricing"),
        label="endpoint pricing",
        error_type=OpenRouterPreflightError,
    )
    prompt_price = _positive_decimal(
        pricing.get("prompt"),
        label="live prompt price",
        error_type=OpenRouterPreflightError,
    )
    completion_price = _positive_decimal(
        pricing.get("completion"),
        label="live completion price",
        error_type=OpenRouterPreflightError,
    )
    return OpenRouterModelSpec(
        model_id=pinned.model_id,
        canonical_slug=pinned.canonical_slug,
        endpoint_tag=pinned.endpoint_tag,
        provider_name=pinned.provider_name,
        quantization=pinned.quantization,
        supported_parameters=pinned.supported_parameters,
        reasoning=pinned.reasoning,
        prompt_price=prompt_price,
        completion_price=completion_price,
    )


def _prompt_bytes(samples: tuple[Any, ...], system_prompt: str | None) -> int:
    if system_prompt is not None and not isinstance(system_prompt, str):
        raise OpenRouterPreflightError("system_prompt must be a string or null")
    system_bytes = len((system_prompt or "").encode("utf-8"))
    total = 0
    for index, sample in enumerate(samples):
        prompt = getattr(sample, "prompt", None)
        if not isinstance(prompt, str):
            raise OpenRouterPreflightError(f"samples[{index}].prompt must be a string")
        total += system_bytes + len(prompt.encode("utf-8"))
    return total


def preflight_openrouter_cohort(
    manifest_path: str | Path,
    samples: Iterable[Any],
    config: GenerationConfig,
    budget: CostBudget,
    get_json: Callable[[str], Any] = _get_json,
    system_prompt: str | None = None,
) -> OpenRouterPreflight:
    """Resolve a pinned cohort using public GETs and enforce its full-sweep budget."""

    pinned_specs = load_cohort_manifest(manifest_path)
    sample_list = tuple(samples)
    if isinstance(config.max_tokens, bool) or not isinstance(config.max_tokens, int):
        raise OpenRouterPreflightError("config.max_tokens must be a positive integer")
    if config.max_tokens <= 0:
        raise OpenRouterPreflightError("config.max_tokens must be a positive integer")
    prompt_bytes = _prompt_bytes(sample_list, system_prompt)

    catalogue = _fetch_public(
        get_json,
        f"{OPENROUTER_API_BASE}/models",
        label="model catalogue",
    )
    resolved_specs = []
    for pinned in pinned_specs:
        _catalogue_entry(catalogue, pinned)
        encoded_model_id = quote(pinned.model_id, safe="/")
        endpoint_payload = _fetch_public(
            get_json,
            f"{OPENROUTER_API_BASE}/models/{encoded_model_id}/endpoints",
            label="model endpoints",
        )
        resolved_specs.append(_live_spec(endpoint_payload, pinned))

    sample_count = len(sample_list)
    projected_usd = sum(
        (
            Decimal(prompt_bytes) * spec.prompt_price
            + Decimal(sample_count * config.max_tokens) * spec.completion_price
            for spec in resolved_specs
        ),
        start=Decimal("0"),
    )
    budget.preflight(projected_usd)
    specs = tuple(resolved_specs)
    return OpenRouterPreflight(
        specs=specs,
        projected_usd=projected_usd,
        model_count=len(specs),
        calls=len(specs) * sample_count,
    )
