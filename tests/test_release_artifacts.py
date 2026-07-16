import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results" / "runs"
PUBLIC_DATA = ROOT / "apps" / "web" / "public" / "data"


def _json_lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_registered_cohorts_contain_complete_real_evaluation_artifacts() -> None:
    reference = json.loads(
        (ROOT / "benchmark" / "models" / "reference-models-2026-07-15.json").read_text(
            encoding="utf-8"
        )
    )
    community = json.loads(
        (ROOT / "benchmark" / "models" / "community-models-2026-07-16.json").read_text(
            encoding="utf-8"
        )
    )
    run_directories = sorted(path for path in RUNS.iterdir() if path.is_dir())

    assert reference["model_count"] == 34
    assert reference["ollama_cloud_model_count"] == 19
    assert reference["openrouter_model_count"] == 15
    assert reference["catalogue_model_count"] == 18
    assert reference["distinct_registry_additions"] == 1
    assert community["model_count"] == 1
    assert len(run_directories) == reference["model_count"] + community["model_count"]

    evaluated_runs = {}
    for run_directory in run_directories:
        run = json.loads((run_directory / "run.json").read_text(encoding="utf-8"))
        summary = json.loads((run_directory / "summary.json").read_text(encoding="utf-8"))
        samples = _json_lines(run_directory / "samples.jsonl")
        scored_samples = _json_lines(run_directory / "scored_samples.jsonl")
        trace_files = sorted((run_directory / "judge-traces").glob("*/*.jsonl"))

        evaluated_runs[run["model"]] = run["run_id"]
        assert run["status"] == "scored"
        assert run["benchmark_version"] == "0.3.0"
        assert run["scorer_version"] == "0.3.1"
        assert run["sample_count"] == 20
        assert len(samples) == 20
        assert len(scored_samples) == 20
        assert len(run["judge_models"]) == 3
        assert len(set(run["judge_models"])) == 3
        assert run["model"] not in run["judge_models"]
        assert len(trace_files) == 3
        assert sum(len(_json_lines(path)) for path in trace_files) == 60
        valid_label_count = sum(
            judge.get("labels") is not None
            for scored_sample in scored_samples
            for judge in scored_sample["judges"]
        )
        assert valid_label_count == sum(
            scored_sample["judge_success_count"] for scored_sample in scored_samples
        )
        assert all(scored_sample["judge_success_count"] >= 2 for scored_sample in scored_samples)
        assert summary["samples_scored"] == 20
        assert summary["tracks"]["en"]["coverage_status"] == "complete"

    assert set(reference["models"]) <= set(evaluated_runs)
    community_runs = {record["model"]: record["run_id"] for record in community["models"]}
    assert {model: evaluated_runs[model] for model in community_runs} == community_runs
    assert set(evaluated_runs) == set(reference["models"]) | set(community_runs)


def test_public_export_matches_registered_cohorts_and_is_provider_neutral() -> None:
    leaderboard = json.loads((PUBLIC_DATA / "leaderboard.json").read_text(encoding="utf-8"))
    public_runs = sorted((PUBLIC_DATA / "runs").glob("*.json"))

    assert len(leaderboard) == 35
    assert len(public_runs) == 35
    assert Counter(entry["result_cohort"] for entry in leaderboard) == {
        "reference": 34,
        "community": 1,
    }
    assert {entry["language"] for entry in leaderboard} == {"en"}
    assert {entry["benchmark_version"] for entry in leaderboard} == {"0.3.0"}
    assert {entry["scorer_version"] for entry in leaderboard} == {"0.3.1"}
    assert {entry["coverage_status"] for entry in leaderboard} == {"complete"}
    assert {entry["samples_scored"] for entry in leaderboard} == {20}
    assert Counter(entry["release_class"] for entry in leaderboard) == {
        "closed_proprietary": 9,
        "open_weights": 18,
        "open_source": 8,
    }
    assert Counter(entry["origin_region"] for entry in leaderboard) == {
        "china": 11,
        "united_states": 19,
        "europe": 3,
        "other": 2,
    }
    assert {entry["taxonomy_classified_at"] for entry in leaderboard} == {"2026-07-16"}
    assert all(entry["taxonomy_source_url"].startswith("https://") for entry in leaderboard)
    esdrac = next(entry for entry in leaderboard if entry["model"] == "esdrac")
    assert esdrac["run_id"] == "20260716T143944Z-esdrac-6bd35957"
    assert esdrac["result_cohort"] == "community"

    public_payload = "\n".join(
        [
            json.dumps(leaderboard),
            *(path.read_text(encoding="utf-8") for path in public_runs),
        ]
    ).lower()
    assert '"provider"' not in public_payload
    assert "human calibration" not in public_payload
    assert "human_review" not in public_payload
