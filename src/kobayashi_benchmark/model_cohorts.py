from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Literal

from .dataset import BENCHMARK_ROOT

REFERENCE_MODELS_PATH = BENCHMARK_ROOT / "models" / "reference-models-2026-07-15.json"
COMMUNITY_MODELS_PATH = BENCHMARK_ROOT / "models" / "community-models-2026-07-16.json"

ResultCohort = Literal["reference", "community"]


@dataclass(frozen=True)
class ModelCohorts:
    by_model: dict[str, ResultCohort]
    community_runs: dict[str, str]


def _load_object(path: Path, name: str) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError(f"Unsupported {name} schema")
    return payload


def _require_text(record: dict[str, object], field: str, context: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty for {context}")
    return value.strip()


def load_model_cohorts(
    reference_models_path: Path = REFERENCE_MODELS_PATH,
    community_models_path: Path = COMMUNITY_MODELS_PATH,
) -> ModelCohorts:
    reference = _load_object(reference_models_path, "reference model manifest")
    reference_models = reference.get("models")
    if not isinstance(reference_models, list) or not all(
        isinstance(model, str) and model.strip() for model in reference_models
    ):
        raise ValueError("Reference model manifest must contain a models list")
    normalized_reference = [model.strip() for model in reference_models]
    if len(set(normalized_reference)) != len(normalized_reference):
        raise ValueError("Duplicate model in reference model manifest")
    if reference.get("model_count") != len(normalized_reference):
        raise ValueError("Reference model_count does not match models list")

    community = _load_object(community_models_path, "community model manifest")
    community_records = community.get("models")
    if not isinstance(community_records, list):
        raise ValueError("Community model manifest must contain a models list")
    if community.get("model_count") != len(community_records):
        raise ValueError("Community model_count does not match models list")

    by_model: dict[str, ResultCohort] = {
        model: "reference" for model in normalized_reference
    }
    community_runs: dict[str, str] = {}
    seen_run_ids: set[str] = set()
    for raw_record in community_records:
        if not isinstance(raw_record, dict):
            raise ValueError("Each community model must be an object")
        model = _require_text(raw_record, "model", "community model")
        if model in community_runs:
            raise ValueError(f"Duplicate community model {model!r}")
        if model in by_model:
            raise ValueError(f"Model {model!r} is both reference and community")
        run_id = _require_text(raw_record, "run_id", model)
        if run_id in seen_run_ids:
            raise ValueError(f"Duplicate community run_id {run_id!r}")
        submission_url = _require_text(raw_record, "submission_url", model)
        if not submission_url.startswith("https://"):
            raise ValueError(f"Community submission_url must use HTTPS for {model!r}")
        accepted_at = _require_text(raw_record, "accepted_at", model)
        try:
            date.fromisoformat(accepted_at)
        except ValueError as error:
            raise ValueError(
                f"Community accepted_at must be an ISO date for {model!r}"
            ) from error
        by_model[model] = "community"
        community_runs[model] = run_id
        seen_run_ids.add(run_id)

    return ModelCohorts(by_model=by_model, community_runs=community_runs)
