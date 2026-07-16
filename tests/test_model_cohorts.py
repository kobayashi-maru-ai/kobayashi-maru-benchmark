import json
from pathlib import Path

import pytest

from kobayashi_benchmark.model_cohorts import load_model_cohorts

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_MODELS = ROOT / "benchmark" / "models" / "reference-models-2026-07-15.json"
COMMUNITY_MODELS = ROOT / "benchmark" / "models" / "community-models-2026-07-16.json"


def test_cohorts_preserve_reference_fleet_and_register_esdrac_run() -> None:
    cohorts = load_model_cohorts()

    assert list(cohorts.by_model.values()).count("reference") == 34
    assert list(cohorts.by_model.values()).count("community") == 1
    assert cohorts.by_model["esdrac"] == "community"
    assert (
        cohorts.community_runs["esdrac"]
        == "20260716T143944Z-esdrac-6bd35957"
    )


def test_cohort_loader_rejects_overlapping_models(tmp_path: Path) -> None:
    community = json.loads(COMMUNITY_MODELS.read_text(encoding="utf-8"))
    community["models"][0]["model"] = "deepseek-v4-flash"
    community_path = tmp_path / "community.json"
    community_path.write_text(json.dumps(community), encoding="utf-8")

    with pytest.raises(ValueError, match="both reference and community"):
        load_model_cohorts(REFERENCE_MODELS, community_path)


def test_cohort_loader_rejects_duplicate_community_run_ids(tmp_path: Path) -> None:
    community = json.loads(COMMUNITY_MODELS.read_text(encoding="utf-8"))
    community["model_count"] = 2
    community["models"].append(
        {
            **community["models"][0],
            "model": "another-model",
        }
    )
    community_path = tmp_path / "community.json"
    community_path.write_text(json.dumps(community), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate community run_id"):
        load_model_cohorts(REFERENCE_MODELS, community_path)


def test_cohort_loader_rejects_duplicate_community_models(tmp_path: Path) -> None:
    community = json.loads(COMMUNITY_MODELS.read_text(encoding="utf-8"))
    community["model_count"] = 2
    community["models"].append(
        {
            **community["models"][0],
            "run_id": "another-run",
        }
    )
    community_path = tmp_path / "community.json"
    community_path.write_text(json.dumps(community), encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate community model"):
        load_model_cohorts(REFERENCE_MODELS, community_path)
