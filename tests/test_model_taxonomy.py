import json
from collections import Counter
from pathlib import Path

import pytest

from kobayashi_benchmark.model_taxonomy import (
    enrich_leaderboard,
    load_model_taxonomy,
)

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_MODELS = ROOT / "benchmark" / "models" / "reference-models-2026-07-15.json"
TAXONOMY = ROOT / "benchmark" / "models" / "model-taxonomy-2026-07-16.json"


def test_taxonomy_covers_the_exact_reference_fleet_with_auditable_metadata() -> None:
    reference = json.loads(REFERENCE_MODELS.read_text(encoding="utf-8"))

    taxonomy = load_model_taxonomy()

    assert set(taxonomy) == set(reference["models"])
    assert len(taxonomy) == reference["model_count"] == 34
    assert Counter(record["release_class"] for record in taxonomy.values()) == {
        "closed_proprietary": 9,
        "open_weights": 18,
        "open_source": 7,
    }
    assert Counter(record["origin_region"] for record in taxonomy.values()) == {
        "china": 11,
        "united_states": 19,
        "europe": 2,
        "other": 2,
    }
    for model, record in taxonomy.items():
        assert record["model"] == model
        assert record["organization"].strip()
        assert record["origin_country"].strip()
        assert record["taxonomy_note"].strip()
        assert record["taxonomy_source_url"].startswith("https://")
        assert record["taxonomy_source_label"].strip()
        assert record["taxonomy_classified_at"] == "2026-07-16"


def test_taxonomy_loader_rejects_incomplete_reference_coverage(tmp_path: Path) -> None:
    reference_path = tmp_path / "reference.json"
    taxonomy_path = tmp_path / "taxonomy.json"
    reference_path.write_text(
        json.dumps({"schema_version": 1, "model_count": 2, "models": ["a", "b"]}),
        encoding="utf-8",
    )
    taxonomy_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "classified_at": "2026-07-16",
                "models": [
                    {
                        "model": "a",
                        "organization": "Lab",
                        "release_class": "open_source",
                        "origin_region": "europe",
                        "origin_country": "France",
                        "source_url": "https://example.com/a",
                        "source_label": "Release",
                        "classification_note": "Apache-2.0 release.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="coverage"):
        load_model_taxonomy(taxonomy_path, reference_path)


def test_taxonomy_loader_rejects_an_invalid_classification_date(tmp_path: Path) -> None:
    taxonomy_payload = json.loads(TAXONOMY.read_text(encoding="utf-8"))
    taxonomy_payload["classified_at"] = "2026-99-99"
    taxonomy_path = tmp_path / "taxonomy.json"
    taxonomy_path.write_text(json.dumps(taxonomy_payload), encoding="utf-8")

    with pytest.raises(ValueError, match="ISO date"):
        load_model_taxonomy(taxonomy_path, REFERENCE_MODELS)


def test_enrichment_preserves_order_and_rejects_unclassified_models() -> None:
    taxonomy = load_model_taxonomy()
    models = ["x-ai/grok-4.5", "deepseek-v4-flash"]

    enriched = enrich_leaderboard([{"model": model, "score": index} for index, model in enumerate(models)])

    assert [entry["model"] for entry in enriched] == models
    assert enriched[0]["release_class"] == "closed_proprietary"
    assert enriched[1]["release_class"] == "open_source"
    assert taxonomy[models[0]]["organization"] == "xAI"

    with pytest.raises(ValueError, match="No taxonomy classification"):
        enrich_leaderboard([{"model": "unclassified/model"}])
