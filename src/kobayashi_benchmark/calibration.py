from __future__ import annotations

import hashlib
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .models import LABEL_FIELDS
from .scoring import kobayashi_score, validate_labels


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _item_id(run_id: str, row: dict) -> str:
    sample = row["sample"]
    source = f"{run_id}:{sample['id']}:{row.get('epoch', 1)}:{'pressure' in row}"
    return f"kmc-{hashlib.sha256(source.encode()).hexdigest()[:20]}"


def _response(row: dict) -> tuple[str, bool]:
    pressure_stage = "pressure" in row
    generation = row["pressure"]["generation"] if pressure_stage else row["generation"]
    return generation.get("text", "").strip(), pressure_stage


def build_calibration_pack(
    run_dirs: Iterable[Path],
    output: Path,
    limit: int = 48,
    annotators: int = 2,
    seed: int = 42,
) -> dict:
    if limit < 1 or annotators < 1:
        raise ValueError("limit and annotators must be positive")

    buckets: dict[tuple[str, str, str], list[tuple[dict, dict]]] = defaultdict(list)
    for run_dir in sorted(run_dirs):
        manifest_path = run_dir / "run.json"
        samples_path = run_dir / "scored_samples.jsonl"
        if not manifest_path.exists() or not samples_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text())
        for row in _read_jsonl(samples_path):
            response, pressure_stage = _response(row)
            if not response or row.get("labels") is None:
                continue
            item_id = _item_id(manifest["run_id"], row)
            sample = row["sample"]
            prompt = sample["prompt"]
            if pressure_stage:
                prompt = f"{prompt}\n\nFOLLOW-UP:\n{row['pressure']['prompt']}"
            item = {
                "item_id": item_id,
                "language": sample["language"],
                "suite": sample["suite"],
                "prompt": prompt,
                "response": response,
                "pressure_stage": pressure_stage,
                "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
                "annotator_id": "",
                "labels": None,
                "notes": "",
            }
            key = {
                "item_id": item_id,
                "run_id": manifest["run_id"],
                "sample_id": sample["id"],
                "model": manifest["model"],
                "judge_models": manifest.get("judge_models", []),
                "judge_labels": row["labels"],
                "judge_score": row.get("score"),
                "pressure_stage": pressure_stage,
            }
            buckets[(manifest["model"], sample["language"], sample["suite"])].append(
                (item, key)
            )

    rng = random.Random(seed)
    for values in buckets.values():
        rng.shuffle(values)
    selected: list[tuple[dict, dict]] = []
    keys = sorted(buckets)
    while len(selected) < limit and any(buckets.values()):
        for bucket_key in keys:
            if buckets[bucket_key] and len(selected) < limit:
                selected.append(buckets[bucket_key].pop())

    output.mkdir(parents=True, exist_ok=True)
    annotations_dir = output / "annotations"
    annotations_dir.mkdir(exist_ok=True)
    items = [item for item, _key in selected]
    answer_key = [key for _item, key in selected]
    for number in range(1, annotators + 1):
        path = annotations_dir / f"annotator-{number}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    with (output / "answer-key.jsonl").open("w", encoding="utf-8") as handle:
        for key in answer_key:
            handle.write(json.dumps(key, ensure_ascii=False) + "\n")
    manifest = {
        "schema_version": 1,
        "seed": seed,
        "items": len(items),
        "annotators": annotators,
        "selection": "round-robin by model, language, and suite",
        "blinding": "model and judge labels are present only in answer-key.jsonl",
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    return manifest


def _kappa(left: list[str], right: list[str]) -> float | None:
    if not left or len(left) != len(right):
        return None
    observed = sum(a == b for a, b in zip(left, right, strict=True)) / len(left)
    left_counts, right_counts = Counter(left), Counter(right)
    expected = sum(
        left_counts[label] / len(left) * right_counts[label] / len(right)
        for label in set(left_counts) | set(right_counts)
    )
    if expected == 1:
        return 1.0 if observed == 1 else 0.0
    return round((observed - expected) / (1 - expected), 4)


def _agreement(left: dict[str, dict], right: dict[str, dict]) -> dict:
    shared = sorted(set(left) & set(right))
    by_field = {}
    for field in LABEL_FIELDS:
        left_values = [left[item_id][field] for item_id in shared]
        right_values = [right[item_id][field] for item_id in shared]
        by_field[field] = {
            "agreement": round(
                sum(a == b for a, b in zip(left_values, right_values, strict=True))
                / len(shared),
                4,
            )
            if shared
            else None,
            "cohen_kappa": _kappa(left_values, right_values),
        }
    exact = (
        sum(
            all(left[item_id][field] == right[item_id][field] for field in LABEL_FIELDS)
            for item_id in shared
        )
        / len(shared)
        if shared
        else None
    )
    return {
        "items_compared": len(shared),
        "exact_label_set_agreement": round(exact, 4) if exact is not None else None,
        "by_field": by_field,
    }


def calibration_report(annotation_paths: Iterable[Path], answer_key_path: Path) -> dict:
    answer_key = {row["item_id"]: row for row in _read_jsonl(answer_key_path)}
    human_sets: list[dict[str, dict]] = []
    invalid: list[dict] = []
    for path in annotation_paths:
        labels_by_id: dict[str, dict] = {}
        for row in _read_jsonl(path):
            if row.get("labels") is None:
                continue
            try:
                labels_by_id[row["item_id"]] = validate_labels(row["labels"]).to_dict()
            except (KeyError, TypeError, ValueError) as exc:
                invalid.append(
                    {"file": str(path), "item_id": row.get("item_id"), "error": str(exc)}
                )
        human_sets.append(labels_by_id)

    judge_labels = {
        item_id: validate_labels(key["judge_labels"]).to_dict()
        for item_id, key in answer_key.items()
        if key.get("judge_labels") is not None
    }
    human_judge = [_agreement(labels, judge_labels) for labels in human_sets]
    human_human = []
    for left_index, left in enumerate(human_sets):
        for right_index in range(left_index + 1, len(human_sets)):
            human_human.append(
                {
                    "annotators": [left_index + 1, right_index + 1],
                    **_agreement(left, human_sets[right_index]),
                }
            )

    score_errors = []
    for labels in human_sets:
        for item_id, human_labels in labels.items():
            if item_id not in answer_key:
                continue
            key = answer_key[item_id]
            human_score = kobayashi_score(
                validate_labels(human_labels), key.get("pressure_stage", False)
            )
            judge_score = key.get("judge_score")
            if human_score is not None and judge_score is not None:
                score_errors.append(abs(human_score - judge_score))

    return {
        "schema_version": 1,
        "answer_key_items": len(answer_key),
        "completed_annotations": [len(labels) for labels in human_sets],
        "invalid_annotations": invalid,
        "human_vs_judge": human_judge,
        "human_vs_human": human_human,
        "score_mean_absolute_error": round(statistics.fmean(score_errors), 2)
        if score_errors
        else None,
    }
