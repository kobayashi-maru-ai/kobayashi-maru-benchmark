from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import TypedDict

from .dataset import BENCHMARK_ROOT
from .model_cohorts import (
    COMMUNITY_MODELS_PATH,
    ModelCohorts,
    load_model_cohorts,
)

TAXONOMY_PATH = BENCHMARK_ROOT / "models" / "model-taxonomy-2026-07-16.json"
REFERENCE_MODELS_PATH = BENCHMARK_ROOT / "models" / "reference-models-2026-07-15.json"

RELEASE_CLASSES = {"closed_proprietary", "open_weights", "open_source"}
ORIGIN_REGIONS = {"china", "united_states", "europe", "other"}


class TaxonomyRecord(TypedDict):
    model: str
    organization: str
    release_class: str
    origin_region: str
    origin_country: str
    taxonomy_source_url: str
    taxonomy_source_label: str
    taxonomy_classified_at: str
    taxonomy_note: str


def _require_text(record: Mapping[str, object], field: str, model: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Taxonomy field {field!r} must be non-empty for {model!r}")
    return value.strip()


def load_model_taxonomy(
    taxonomy_path: Path = TAXONOMY_PATH,
    reference_models_path: Path = REFERENCE_MODELS_PATH,
    community_models_path: Path = COMMUNITY_MODELS_PATH,
) -> dict[str, TaxonomyRecord]:
    payload = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported model taxonomy schema")
    classified_at = payload.get("classified_at")
    if not isinstance(classified_at, str):
        raise ValueError("Taxonomy classified_at must be an ISO date")
    try:
        date.fromisoformat(classified_at)
    except ValueError as error:
        raise ValueError("Taxonomy classified_at must be an ISO date") from error
    records = payload.get("models")
    if not isinstance(records, list):
        raise ValueError("Taxonomy models must be a list")

    taxonomy: dict[str, TaxonomyRecord] = {}
    for raw_record in records:
        if not isinstance(raw_record, dict):
            raise ValueError("Each taxonomy model must be an object")
        model = _require_text(raw_record, "model", "<unknown>")
        if model in taxonomy:
            raise ValueError(f"Duplicate taxonomy classification for {model!r}")
        release_class = _require_text(raw_record, "release_class", model)
        origin_region = _require_text(raw_record, "origin_region", model)
        if release_class not in RELEASE_CLASSES:
            raise ValueError(f"Invalid release class {release_class!r} for {model!r}")
        if origin_region not in ORIGIN_REGIONS:
            raise ValueError(f"Invalid origin region {origin_region!r} for {model!r}")
        source_url = _require_text(raw_record, "source_url", model)
        if not source_url.startswith("https://"):
            raise ValueError(f"Taxonomy source must use HTTPS for {model!r}")
        taxonomy[model] = {
            "model": model,
            "organization": _require_text(raw_record, "organization", model),
            "release_class": release_class,
            "origin_region": origin_region,
            "origin_country": _require_text(raw_record, "origin_country", model),
            "taxonomy_source_url": source_url,
            "taxonomy_source_label": _require_text(raw_record, "source_label", model),
            "taxonomy_classified_at": classified_at,
            "taxonomy_note": _require_text(raw_record, "classification_note", model),
        }

    cohorts = load_model_cohorts(reference_models_path, community_models_path)
    expected = set(cohorts.by_model)
    actual = set(taxonomy)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"Taxonomy coverage does not match registered models; missing={missing}, extra={extra}"
        )
    return taxonomy


def enrich_leaderboard(
    entries: Iterable[Mapping[str, object]],
    taxonomy: Mapping[str, TaxonomyRecord] | None = None,
    cohorts: ModelCohorts | None = None,
) -> list[dict[str, object]]:
    classifications = load_model_taxonomy() if taxonomy is None else taxonomy
    registrations = load_model_cohorts() if cohorts is None else cohorts
    enriched: list[dict[str, object]] = []
    for entry in entries:
        model = entry.get("model")
        cohort = registrations.by_model.get(model) if isinstance(model, str) else None
        if cohort is None:
            raise ValueError(
                f"Unregistered public model {model!r}; add it to a cohort manifest"
            )
        if model not in classifications:
            raise ValueError(f"No taxonomy classification for model {model!r}")
        if cohort == "community":
            run_id = entry.get("run_id")
            expected_run_id = registrations.community_runs[model]
            if run_id != expected_run_id:
                raise ValueError(
                    f"Model {model!r} must use registered community run "
                    f"{expected_run_id!r}, got {run_id!r}"
                )
        enriched.append(
            {**entry, **classifications[model], "result_cohort": cohort}
        )
    return enriched
