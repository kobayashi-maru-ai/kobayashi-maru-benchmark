from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol

from .models import GenerationConfig, GenerationResult


class ModelAdapter(Protocol):
    provider: str
    model: str

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult: ...


class BudgetExceeded(RuntimeError):
    """Raised when a projected or actual cost reaches the exclusive budget limit."""


class CostBudget:
    def __init__(self, limit: Decimal) -> None:
        self._validate_amount(limit, name="limit")
        if limit == 0:
            raise ValueError("limit must be greater than zero")
        self._limit = limit
        self._spent = Decimal("0")

    @property
    def limit(self) -> Decimal:
        return self._limit

    @property
    def spent(self) -> Decimal:
        return self._spent

    @staticmethod
    def _validate_amount(amount: Decimal, *, name: str) -> None:
        if not isinstance(amount, Decimal):
            raise TypeError(f"{name} must be a Decimal")
        if not amount.is_finite():
            raise ValueError(f"{name} must be finite")
        if amount < 0:
            raise ValueError(f"{name} must not be negative")

    def _require_below_limit(self, projected_spend: Decimal) -> None:
        if projected_spend >= self.limit:
            raise BudgetExceeded(
                f"projected spend {projected_spend} must remain below limit {self.limit}"
            )

    def preflight(self, projected_total: Decimal) -> None:
        self._validate_amount(projected_total, name="projected_total")
        self._require_below_limit(projected_total)

    def authorize(self, projected_request: Decimal) -> None:
        self._validate_amount(projected_request, name="projected_request")
        self._require_below_limit(self.spent + projected_request)

    def charge(self, actual_cost: Decimal) -> Decimal:
        self._validate_amount(actual_cost, name="actual_cost")
        cumulative_cost = self.spent + actual_cost
        self._require_below_limit(cumulative_cost)
        self._spent = cumulative_cost
        return self.spent


@dataclass(frozen=True)
class OpenRouterModelSpec:
    model_id: str
    canonical_slug: str
    endpoint_tag: str
    quantization: str
    supported_parameters: frozenset[str]
    reasoning: dict[str, Any] | None
    prompt_price: Decimal
    completion_price: Decimal

    def __post_init__(self) -> None:
        required_strings = {
            "model_id": self.model_id,
            "canonical_slug": self.canonical_slug,
            "endpoint_tag": self.endpoint_tag,
            "quantization": self.quantization,
        }
        for name, value in required_strings.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.supported_parameters, frozenset):
            raise TypeError("supported_parameters must be a frozenset")
        CostBudget._validate_amount(self.prompt_price, name="prompt_price")
        CostBudget._validate_amount(self.completion_price, name="completion_price")


@dataclass
class OpenRouterAdapter:
    spec: OpenRouterModelSpec
    api_key: str
    budget: CostBudget
    base_url: str = "https://openrouter.ai/api/v1"
    timeout: int = 300
    provider: str = "openrouter"

    @property
    def model(self) -> str:
        return self.spec.model_id

    def _result_error(self, started: float, message: str) -> GenerationResult:
        return GenerationResult(
            text="",
            latency_ms=round((time.perf_counter() - started) * 1000),
            error=message[:120],
        )

    def _projected_request_cost(
        self, prompt: str, system_prompt: str | None, max_tokens: int
    ) -> Decimal:
        prompt_bytes = len(prompt.encode("utf-8"))
        if system_prompt:
            prompt_bytes += len(system_prompt.encode("utf-8"))
        return (
            Decimal(prompt_bytes) * self.spec.prompt_price
            + Decimal(max_tokens) * self.spec.completion_price
        )

    def _payload(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None
    ) -> tuple[dict[str, Any], list[str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload: dict[str, Any] = {
            "model": self.spec.canonical_slug,
            "messages": messages,
            "stream": False,
            "provider": {
                "only": [self.spec.endpoint_tag],
                "allow_fallbacks": False,
                "require_parameters": True,
                "data_collection": "deny",
            },
        }
        configurable = {
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
            "seed": config.seed,
        }
        request_parameters = []
        for name, value in configurable.items():
            if name in self.spec.supported_parameters:
                payload[name] = value
                request_parameters.append(name)
        if self.spec.reasoning is not None:
            if "reasoning" not in self.spec.supported_parameters:
                raise ValueError("pinned reasoning configuration is unsupported")
            payload["reasoning"] = dict(self.spec.reasoning)
            request_parameters.append("reasoning")
        return payload, sorted(request_parameters)

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult:
        started = time.perf_counter()
        try:
            self.budget.authorize(
                self._projected_request_cost(prompt, system_prompt, config.max_tokens)
            )
            payload, request_parameters = self._payload(prompt, config, system_prompt)
        except BudgetExceeded:
            return self._result_error(started, "BudgetExceeded: budget authorization refused")
        except (TypeError, ValueError):
            return self._result_error(started, "OpenRouter unsupported configuration")

        try:
            data = _post_json(
                f"{self.base_url.rstrip('/')}/chat/completions",
                payload,
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "X-OpenRouter-Metadata": "enabled",
                },
                self.timeout,
            )
        except urllib.error.HTTPError as exc:
            return self._result_error(started, f"OpenRouter HTTP {exc.code}")
        except (OSError, ValueError) as exc:
            return self._result_error(started, f"OpenRouter network {type(exc).__name__}")

        if not isinstance(data, dict):
            return self._result_error(started, "OpenRouter malformed response")
        provider_error = data.get("error")
        if provider_error is not None:
            code = provider_error.get("code") if isinstance(provider_error, dict) else None
            suffix = f" {code}" if isinstance(code, int) else ""
            return self._result_error(started, f"OpenRouter provider error{suffix}")

        usage = data.get("usage")
        if not isinstance(usage, dict) or "cost" not in usage:
            return self._result_error(started, "OpenRouter missing billed cost")
        try:
            billed_cost = Decimal(str(usage["cost"]))
            self.budget.charge(billed_cost)
        except (TypeError, ValueError, ArithmeticError):
            return self._result_error(started, "OpenRouter invalid billed cost")
        except BudgetExceeded:
            return self._result_error(started, "BudgetExceeded: billed cost exceeds budget")

        returned_model = data.get("model")
        allowed_identities = {self.spec.model_id, self.spec.canonical_slug}
        if returned_model not in allowed_identities:
            return self._result_error(started, "OpenRouter identity mismatch")

        choices = data.get("choices")
        choice = choices[0] if isinstance(choices, list) and choices else {}
        message = choice.get("message") if isinstance(choice, dict) else {}
        content = message.get("content", "") if isinstance(message, dict) else ""
        if not isinstance(content, str) or not content.strip():
            return self._result_error(started, "empty final response")

        prompt_details = usage.get("prompt_tokens_details")
        completion_details = usage.get("completion_tokens_details")
        prompt_details = prompt_details if isinstance(prompt_details, dict) else {}
        completion_details = completion_details if isinstance(completion_details, dict) else {}
        metadata = {
            "generation_id": data.get("id"),
            "returned_model": returned_model,
            "canonical_model": self.spec.canonical_slug,
            "endpoint_tag": self.spec.endpoint_tag,
            "quantization": self.spec.quantization,
            "done_reason": choice.get("finish_reason"),
            "native_finish_reason": choice.get("native_finish_reason"),
            "system_fingerprint": data.get("system_fingerprint"),
            "service_tier": data.get("service_tier"),
            "thinking_mode": self.spec.reasoning,
            "reasoning_tokens": completion_details.get("reasoning_tokens"),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "cached_tokens": prompt_details.get("cached_tokens"),
            "billed_usd": str(billed_cost),
            "openrouter_metadata": data.get("openrouter_metadata"),
            "request_parameters": request_parameters,
        }
        return GenerationResult(
            text=content,
            latency_ms=round((time.perf_counter() - started) * 1000),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            provider_metadata=metadata,
        )


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: int) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


@dataclass
class OllamaAdapter:
    model: str
    base_url: str = "http://127.0.0.1:11434"
    api_key: str | None = None
    timeout: int = 300
    provider: str = "ollama"

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        started = time.perf_counter()
        try:
            think: bool | str = False
            if config.thinking == "enabled":
                think = True
            elif config.thinking in {"low", "medium", "high"}:
                think = config.thinking
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            data = _post_json(
                f"{self.base_url.rstrip('/')}/api/chat",
                {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "think": think,
                    "options": {
                        "temperature": config.temperature,
                        "top_p": config.top_p,
                        "seed": config.seed,
                        "num_predict": config.max_tokens,
                    },
                },
                headers,
                self.timeout,
            )
            message = data.get("message", {})
            content = message.get("content", "")
            thinking = message.get("thinking", "")
            error = None
            if not content.strip():
                error = "empty final response"
                if thinking:
                    error += " (thinking exhausted the generation budget)"
            return GenerationResult(
                text=content,
                latency_ms=round((time.perf_counter() - started) * 1000),
                prompt_tokens=data.get("prompt_eval_count"),
                completion_tokens=data.get("eval_count"),
                error=error,
                provider_metadata={
                    "done_reason": data.get("done_reason"),
                    "thinking_chars": len(thinking),
                    "thinking_mode": config.thinking,
                },
            )
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000),
                error=f"{type(exc).__name__}: {exc}",
            )


@dataclass
class OpenAICompatibleAdapter:
    model: str
    base_url: str
    api_key: str | None = None
    timeout: int = 300
    provider: str = "openai-compatible"

    def generate(
        self, prompt: str, config: GenerationConfig, system_prompt: str | None = None
    ) -> GenerationResult:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        started = time.perf_counter()
        try:
            data = _post_json(
                f"{self.base_url.rstrip('/')}/chat/completions",
                {
                    "model": self.model,
                    "messages": messages,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "max_tokens": config.max_tokens,
                    "seed": config.seed,
                },
                headers,
                self.timeout,
            )
            usage = data.get("usage", {})
            return GenerationResult(
                text=data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                latency_ms=round((time.perf_counter() - started) * 1000),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                provider_metadata={"id": data.get("id")},
            )
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            return GenerationResult(
                text="",
                latency_ms=round((time.perf_counter() - started) * 1000),
                error=f"{type(exc).__name__}: {exc}",
            )
