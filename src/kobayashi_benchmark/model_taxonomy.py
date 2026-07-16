from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import TypedDict

from .dataset import BENCHMARK_ROOT

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
) -> dict[str, TaxonomyRecord]:
    payload = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_models_path.read_text(encoding="utf-8"))
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

    expected_models = reference.get("models")
    if not isinstance(expected_models, list):
        raise ValueError("Reference model manifest must contain a models list")
    expected = set(expected_models)
    actual = set(taxonomy)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"Taxonomy coverage does not match reference fleet; missing={missing}, extra={extra}"
        )
    if reference.get("model_count") != len(expected) or len(expected) != len(actual):
        raise ValueError("Taxonomy coverage count does not match reference fleet")
    return taxonomy


def enrich_leaderboard(
    entries: Iterable[Mapping[str, object]],
    taxonomy: Mapping[str, TaxonomyRecord] | None = None,
) -> list[dict[str, object]]:
    classifications = taxonomy or load_model_taxonomy()
    enriched: list[dict[str, object]] = []
    for entry in entries:
        model = entry.get("model")
        if not isinstance(model, str) or model not in classifications:
            raise ValueError(f"No taxonomy classification for model {model!r}")
        enriched.append({**entry, **classifications[model]})
    return enriched
