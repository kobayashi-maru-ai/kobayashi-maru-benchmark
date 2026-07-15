from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from dataclasses import replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from .adapters import (
    CostBudget,
    OllamaAdapter,
    OpenAICompatibleAdapter,
    OpenRouterAdapter,
    OpenRouterModelSpec,
)
from .dataset import (
    BENCHMARK_ROOT,
    BENCHMARK_VERSION,
    build_samples,
    filter_samples,
    pilot_samples,
    write_dataset,
)
from .models import GenerationConfig, GenerationResult
from .openrouter import preflight_openrouter_cohort
from .protocol import build_public_protocol
from .reporting import build_leaderboard, build_public_run, summarize
from .runner import EMPTY_FINAL_RETRY_MAX_TOKENS, create_run, retry_empty_final
from .scoring import (
    JUDGE_MAX_TOKENS,
    JUDGE_SYSTEM,
    classify_with_judge,
    judge_prompt,
    kobayashi_score,
    majority_labels,
    validate_labels,
)

SCORER_VERSION = "0.3.1"


def _sweep_budget(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise argparse.ArgumentTypeError(
            "must be a decimal greater than 0 and at most 5"
        ) from None
    if not amount.is_finite() or amount <= 0 or amount > Decimal("5"):
        raise argparse.ArgumentTypeError("must be a decimal greater than 0 and at most 5")
    return amount


def _prior_spend(value: str) -> Decimal:
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError):
        raise argparse.ArgumentTypeError(
            "must be a decimal greater than or equal to 0 and below 5"
        ) from None
    if not amount.is_finite() or amount < 0 or amount >= Decimal("5"):
        raise argparse.ArgumentTypeError(
            "must be a decimal greater than or equal to 0 and below 5"
        )
    return amount


def _repair_max_tokens(value: str) -> int:
    try:
        amount = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer greater than 1024") from None
    if amount <= 1024:
        raise argparse.ArgumentTypeError("must be an integer greater than 1024")
    return amount


def _reject_direct_api_key(_value: str) -> str:
    raise argparse.ArgumentTypeError(
        "direct API keys are forbidden; use --api-key-env"
    )


def _environment_name(value: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value) is None:
        raise argparse.ArgumentTypeError("must be a valid environment variable name")
    return value


def _reasoning_condition(spec: OpenRouterModelSpec) -> str:
    reasoning = spec.reasoning
    if not reasoning:
        return "disabled"
    if "effort" in reasoning:
        effort = reasoning["effort"]
        return "disabled" if effort in {None, "none"} else str(effort)
    if "max_tokens" in reasoning:
        return f"max_tokens={reasoning['max_tokens']}"
    if reasoning.get("enabled") is True:
        return "enabled"
    return "disabled"


def _print_json_line(payload: dict) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        flush=True,
    )


def _project_openrouter_specs(
    specs: tuple[OpenRouterModelSpec, ...], samples: list, config: GenerationConfig
) -> Decimal:
    prompt_bytes = sum(len(sample.prompt.encode("utf-8")) for sample in samples)
    sample_count = len(samples)
    return sum(
        (
            Decimal(prompt_bytes) * spec.prompt_price
            + Decimal(sample_count * config.max_tokens) * spec.completion_price
            for spec in specs
        ),
        start=Decimal("0"),
    )


def command_sweep_openrouter(args) -> int:
    samples = pilot_samples(build_samples())
    budget = CostBudget(args.budget_usd)
    preflight_config = GenerationConfig(
        temperature=0.0,
        top_p=1.0,
        max_tokens=1024,
        seed=42,
        thinking="disabled",
    )
    preflight = preflight_openrouter_cohort(
        manifest_path=args.manifest,
        samples=samples,
        config=preflight_config,
        budget=budget,
    )
    specs = preflight.specs
    selected_model = args.only_model or args.start_at_model
    if selected_model is not None:
        start_index = next(
            (
                index
                for index, spec in enumerate(specs)
                if spec.model_id == selected_model
            ),
            None,
        )
        if start_index is None:
            raise SystemExit("Selected model is not present in the pinned cohort")
        specs = specs[start_index : start_index + 1] if args.only_model else specs[start_index:]
    selected_projection = _project_openrouter_specs(specs, samples, preflight_config)
    budget.preflight(args.prior_spend_usd + selected_projection)
    budget.charge(args.prior_spend_usd)
    projection = {
        "models": preflight.model_count,
        "calls": preflight.calls,
        "projected_usd": str(preflight.projected_usd),
        "budget_usd": str(budget.limit),
    }
    if args.start_at_model is not None or args.only_model is not None or args.prior_spend_usd:
        projection.update(
            {
                "selected_models": len(specs),
                "selected_calls": len(specs) * len(samples),
                "selected_projected_usd": str(selected_projection),
                "prior_spend_usd": str(args.prior_spend_usd),
            }
        )
    _print_json_line(projection)
    if args.preflight_only:
        return 0

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit("Required API key environment variable is not set")

    runs = []
    errors = 0
    for spec in specs:
        adapter = OpenRouterAdapter(spec=spec, api_key=api_key, budget=budget)
        config = GenerationConfig(
            temperature=0.0,
            top_p=1.0,
            max_tokens=1024,
            seed=42,
            thinking=_reasoning_condition(spec),
        )
        run_dir = create_run(
            adapter,
            samples,
            config,
            Path(args.output),
            model_revision=spec.canonical_slug,
            quantization=spec.quantization,
            protocol="core",
            visibility="public",
            fail_fast=True,
        )
        runs.append(run_dir.name)
        manifest = json.loads((run_dir / "run.json").read_text())
        if manifest.get("status") == "failed":
            errors = 1
            break

    summary = {
        "models": preflight.model_count,
        "calls": preflight.calls,
        "projected_usd": str(preflight.projected_usd),
        "actual_usd": str(budget.spent),
        "budget_usd": str(budget.limit),
        "runs": runs,
        "errors": errors,
    }
    if args.start_at_model is not None or args.only_model is not None or args.prior_spend_usd:
        summary.update(
            {
                "start_at_model": args.start_at_model,
                "only_model": args.only_model,
                "prior_spend_usd": str(args.prior_spend_usd),
            }
        )
    _print_json_line(summary)
    return 1 if errors else 0


def _is_official_ollama_cloud(base_url: str) -> bool:
    try:
        parsed = urlsplit(base_url)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname == "ollama.com"
        and port in {None, 443}
        and parsed.path.rstrip("/") == ""
        and not parsed.query
        and not parsed.fragment
    )


def _ollama_api_key(base_url: str, explicit_env: str | None) -> str | None:
    api_key_env = explicit_env or (
        "OLLAMA_API_KEY" if _is_official_ollama_cloud(base_url) else None
    )
    return os.getenv(api_key_env) if api_key_env else None


def _adapter(args, prefix: str = ""):
    adapter_name = getattr(args, f"{prefix}adapter")
    model = getattr(args, f"{prefix}model")
    base_url = getattr(args, f"{prefix}base_url", None)
    if adapter_name == "ollama":
        resolved_base_url = base_url or "http://127.0.0.1:11434"
        return OllamaAdapter(
            model=model,
            base_url=resolved_base_url,
            api_key=_ollama_api_key(
                resolved_base_url, getattr(args, f"{prefix}api_key_env", None)
            ),
            provider=(
                "ollama-cloud"
                if _is_official_ollama_cloud(resolved_base_url)
                else "ollama"
            ),
        )
    api_key_env = getattr(args, f"{prefix}api_key_env", None) or "OPENAI_API_KEY"
    api_key = os.getenv(api_key_env)
    return OpenAICompatibleAdapter(
        model=model,
        base_url=base_url or "https://api.openai.com/v1",
        api_key=api_key,
    )


def command_dataset(args) -> int:
    samples = build_samples()
    counts = write_dataset(Path(args.output), samples)
    print(json.dumps({"total": sum(counts.values()), "suites": counts}, indent=2))
    return 0


def command_run(args) -> int:
    samples = filter_samples(
        build_samples(),
        suites=set(args.suite) if args.suite else None,
        languages=set(args.language) if args.language else None,
        paraphrases=set(args.paraphrase) if args.paraphrase else None,
    )
    if args.profile == "core-20":
        samples = pilot_samples(samples)
    if args.limit:
        samples = samples[: args.limit]
    if not samples:
        raise SystemExit("No samples match the selected filters")
    run_dir = create_run(
        _adapter(args),
        samples,
        GenerationConfig(
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens,
            seed=args.seed,
            thinking=args.thinking,
        ),
        Path(args.output),
        repeats=args.repeats,
        model_revision=args.model_revision,
        quantization=args.quantization,
        system_prompt=args.system_prompt,
        protocol=args.protocol,
        visibility=args.visibility,
    )
    print(run_dir)
    return 0


def command_repair_empty(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "run.json"
    samples_path = run_dir / "samples.jsonl"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("provider") not in {"ollama", "ollama-cloud"}:
        raise SystemExit("repair-empty currently supports Ollama runs only")
    if manifest.get("scorer_version") is not None:
        raise SystemExit("Repair generation errors before scoring the run")

    adapter = OllamaAdapter(
        model=manifest["model"],
        base_url=args.base_url,
        api_key=_ollama_api_key(args.base_url, args.api_key_env),
        provider=(
            "ollama-cloud" if _is_official_ollama_cloud(args.base_url) else "ollama"
        ),
    )
    config = GenerationConfig(**manifest["generation_config"])
    rows = [json.loads(line) for line in samples_path.read_text().splitlines()]
    repaired_count = 0
    for row in rows:
        prior_repair = row.get("generation_repair")
        if prior_repair and not prior_repair.get("attempt_configs"):
            prior_repair["attempt_configs"] = [
                config.to_dict(),
                prior_repair["repair_config"],
            ]
        initial = row["generation"]
        initial_result = GenerationResult(**initial)
        result, repair = retry_empty_final(
            adapter,
            row["sample"]["prompt"],
            config,
            manifest.get("system_prompt"),
            initial_result,
            prior_repair=prior_repair,
        )
        if repair:
            row["generation"] = result.to_dict()
            row["generation_repair"] = repair
            repaired_count += 1

    with samples_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest["generation_repair_policy"] = {
        "trigger": "empty final response caused by hidden-thinking budget exhaustion",
        "max_attempts": 3 if adapter.model.startswith("gpt-oss") else 2,
        "retry_max_tokens": EMPTY_FINAL_RETRY_MAX_TOKENS,
        "final_attempt_adjustment": (
            "If GPT-OSS still returns empty, one final attempt uses thinking=low, "
            "its minimum explicit reasoning level."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"run": manifest["run_id"], "repaired_samples": repaired_count}))
    return 0


def command_repair_openrouter_truncated(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "run.json"
    samples_path = run_dir / "samples.jsonl"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("provider") != "openrouter":
        raise SystemExit("Truncation repair requires an OpenRouter run")

    rows = [json.loads(line) for line in samples_path.read_text().splitlines() if line]
    matches = [
        (index, row)
        for index, row in enumerate(rows)
        if row.get("sample", {}).get("id") == args.sample_id
    ]
    if len(matches) != 1:
        raise SystemExit("Repair sample must occur exactly once in the run")
    row_index, row = matches[0]
    original_generation = row.get("generation")
    if not isinstance(original_generation, dict):
        raise SystemExit("Repair sample generation is malformed")
    original_metadata = original_generation.get("provider_metadata")
    if (
        original_generation.get("error") is not None
        or not isinstance(original_generation.get("text"), str)
        or not original_generation["text"].strip()
        or not isinstance(original_metadata, dict)
        or original_metadata.get("done_reason") != "length"
    ):
        raise SystemExit("Repair requires a non-empty generation truncated by length")

    dataset_matches = [
        sample for sample in pilot_samples(build_samples()) if sample.id == args.sample_id
    ]
    if len(dataset_matches) != 1 or row.get("sample") != dataset_matches[0].to_dict():
        raise SystemExit("Repair sample does not match the pinned core dataset")
    sample = dataset_matches[0]

    original_config = GenerationConfig(**manifest["generation_config"])
    repair_config = replace(original_config, max_tokens=args.max_tokens)
    budget = CostBudget(args.budget_usd)
    preflight = preflight_openrouter_cohort(
        manifest_path=args.manifest,
        samples=[sample],
        config=repair_config,
        budget=budget,
    )
    budget.preflight(args.prior_spend_usd + preflight.projected_usd)
    budget.charge(args.prior_spend_usd)
    specs = [spec for spec in preflight.specs if spec.model_id == manifest.get("model")]
    if len(specs) != 1 or specs[0].canonical_slug != manifest.get("model_revision"):
        raise SystemExit("Run identity does not match the pinned OpenRouter cohort")

    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit("Required API key environment variable is not set")
    result = OpenRouterAdapter(spec=specs[0], api_key=api_key, budget=budget).generate(
        sample.prompt,
        repair_config,
    )
    done_reason = result.provider_metadata.get("done_reason")
    if result.error or not result.text.strip() or done_reason == "length":
        _print_json_line(
            {
                "model": manifest.get("model"),
                "sample_id": args.sample_id,
                "actual_usd": str(budget.spent),
                "error": result.error or "repair remained truncated",
            }
        )
        return 1

    row["generation"] = result.to_dict()
    row["generation_repair"] = {
        "reason": "scoring coverage repair for a length-truncated final response",
        "max_attempts": 2,
        "attempts": [original_generation, result.to_dict()],
        "attempt_configs": [original_config.to_dict(), repair_config.to_dict()],
        "original_generation": original_generation,
        "original_config": original_config.to_dict(),
        "repair_config": repair_config.to_dict(),
    }
    rows[row_index] = row
    samples_path.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in rows)
    )

    manifest["status"] = "generated"
    manifest["scorer_version"] = None
    manifest["verification"] = "three-judge-pending-after-generation-repair"
    for field in ("judge_models", "scoring_policy"):
        manifest.pop(field, None)
    repairs = manifest.setdefault("generation_repairs", [])
    repairs.append(
        {
            "sample_id": args.sample_id,
            "reason": row["generation_repair"]["reason"],
            "original_max_tokens": original_config.max_tokens,
            "repair_max_tokens": repair_config.max_tokens,
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for stale_name in ("summary.json", "scored_samples.jsonl"):
        (run_dir / stale_name).unlink(missing_ok=True)

    _print_json_line(
        {
            "model": manifest["model"],
            "sample_id": args.sample_id,
            "actual_usd": str(budget.spent),
            "repair_billed_usd": str(budget.spent - args.prior_spend_usd),
        }
    )
    return 0


def command_score(args) -> int:
    run_dir = Path(args.run)
    manifest_path = run_dir / "run.json"
    manifest = json.loads(manifest_path.read_text())
    rows = [json.loads(line) for line in (run_dir / "samples.jsonl").read_text().splitlines()]
    if len(args.judge_ollama) != 3 or len(set(args.judge_ollama)) != 3:
        raise SystemExit("Scoring requires exactly three distinct --judge-ollama models")
    if not args.allow_self_judge and manifest["model"] in args.judge_ollama:
        raise SystemExit(
            f"Refusing self-judging panel: {manifest['model']} is the evaluated model"
        )
    judge_api_key = _ollama_api_key(args.judge_base_url, args.judge_api_key_env)
    judge_provider = (
        "ollama-cloud"
        if _is_official_ollama_cloud(args.judge_base_url)
        else "ollama"
    )
    judges = [
        OllamaAdapter(
            model=model,
            base_url=args.judge_base_url,
            api_key=judge_api_key,
            provider=judge_provider,
        )
        for model in args.judge_ollama
    ]
    if args.min_judges < 1 or args.min_judges > len(judges):
        raise SystemExit("--min-judges must be between 1 and the panel size")
    if args.judge_max_attempts < 1:
        raise SystemExit("--judge-max-attempts must be at least 1")

    judgements_by_row: list[list[tuple]] = [[] for _row in rows]
    traces_root = run_dir / "judge-traces" / f"v{SCORER_VERSION}"
    traces_root.mkdir(parents=True, exist_ok=True)
    for judge_index, judge in enumerate(judges, start=1):
        safe_judge = re.sub(r"[^a-zA-Z0-9_.-]+", "-", judge.model).strip("-")
        trace_path = traces_root / f"{safe_judge}.jsonl"
        cached = []
        if trace_path.exists():
            cached = [
                json.loads(line) for line in trace_path.read_text().splitlines() if line.strip()
            ]
        with trace_path.open("w", encoding="utf-8") as trace_handle:
            for row_index, row in enumerate(rows):
                pressure_stage = "pressure" in row
                generation = (
                    row["pressure"]["generation"] if pressure_stage else row["generation"]
                )
                response = generation.get("text", "").strip()
                cache_key = {
                    "sample_id": row["sample"]["id"],
                    "epoch": row.get("epoch", 1),
                    "pressure_stage": pressure_stage,
                    "response_sha256": hashlib.sha256(response.encode()).hexdigest(),
                    "judge_protocol_sha256": hashlib.sha256(
                        (JUDGE_SYSTEM + "\n" + judge_prompt(
                            row["sample"]["prompt"], response, pressure_stage
                        )).encode()
                    ).hexdigest(),
                }
                cached_row = cached[row_index] if row_index < len(cached) else None
                cached_matches = cached_row and all(
                    cached_row.get(key) == value for key, value in cache_key.items()
                )
                if generation.get("error") or not response:
                    judgement = (
                        None,
                        {
                            "judge": judge.model,
                            "provider": judge.provider,
                            "skipped": "generation unavailable",
                        },
                    )
                elif cached_matches and cached_row.get("label") is not None:
                    label_data = cached_row.get("label")
                    judgement = (
                        validate_labels(label_data),
                        cached_row["trace"],
                    )
                else:
                    judgement = classify_with_judge(
                        judge,
                        row["sample"]["prompt"],
                        response,
                        pressure_stage,
                        max_attempts=args.judge_max_attempts,
                    )
                label, trace = judgement
                trace_handle.write(
                    json.dumps(
                        {
                            **cache_key,
                            "label": label.to_dict() if label else None,
                            "trace": trace,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                trace_handle.flush()
                judgements_by_row[row_index].append(judgement)
                print(
                    f"judge {judge_index}/{len(judges)} {judge.model}: "
                    f"{row_index + 1}/{len(rows)}",
                    file=sys.stderr,
                )

    scored_rows = []
    for index, row in enumerate(rows, start=1):
        pressure_stage = "pressure" in row
        generation = row["pressure"]["generation"] if pressure_stage else row["generation"]
        if generation.get("error") or not generation.get("text", "").strip():
            row.update({"judges": [], "labels": None, "judge_agreement": None, "score": None})
        else:
            judgements = judgements_by_row[index - 1]
            successful_labels = [
                label for label, _trace in judgements if label is not None
            ]
            if len(successful_labels) >= args.min_judges:
                rotation_key = (
                    f"{row['sample']['id']}:{row.get('epoch', 1)}:{int(pressure_stage)}"
                )
                rotation = int.from_bytes(
                    hashlib.sha256(rotation_key.encode()).digest()[:8], "big"
                )
                tie_breaker = successful_labels[rotation % len(successful_labels)]
                labels, agreement = majority_labels(
                    successful_labels, tie_breaker=tie_breaker
                )
            else:
                labels, agreement = None, 0.0
            row.update(
                {
                    "judges": [trace for _label, trace in judgements],
                    "labels": labels.to_dict() if labels else None,
                    "judge_agreement": agreement if labels else None,
                    "judge_success_count": len(successful_labels),
                    "score": kobayashi_score(labels, pressure_stage) if labels else None,
                }
            )
        scored_rows.append(row)
        print(f"scored {index}/{len(rows)}", file=sys.stderr)
    with (run_dir / "scored_samples.jsonl").open("w", encoding="utf-8") as handle:
        for row in scored_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = summarize(scored_rows)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    manifest.update(
        {
            "status": "scored",
            "scorer_version": SCORER_VERSION,
            "judge_models": [judge.model for judge in judges],
            "scoring_policy": {
                "min_judges": args.min_judges,
                "self_judging_allowed": args.allow_self_judge,
                "invalid_json_max_attempts": args.judge_max_attempts,
                "judge_generation": {
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_tokens": JUDGE_MAX_TOKENS,
                    "seed": 42,
                    "thinking": "low for gpt-oss; disabled otherwise",
                },
            },
            "verification": "three-judge-evaluated",
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def command_leaderboard(args) -> int:
    entries = build_leaderboard(Path(args.results).glob("*"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(entries)} entries to {output}")
    return 0


def command_export_web(args) -> int:
    output = Path(args.output)
    runs_output = output / "runs"
    if runs_output.exists():
        shutil.rmtree(runs_output)
    runs_output.mkdir(parents=True, exist_ok=True)
    run_dirs = list(Path(args.results).glob("*"))
    leaderboard = build_leaderboard(run_dirs)
    (output / "leaderboard.json").write_text(
        json.dumps(leaderboard, indent=2, ensure_ascii=False) + "\n"
    )
    (output / "protocol.json").write_text(
        json.dumps(build_public_protocol(), indent=2, ensure_ascii=False) + "\n"
    )
    exported = 0
    for run_dir in run_dirs:
        public_run = build_public_run(run_dir)
        if public_run is None:
            continue
        run_id = public_run["run"]["run_id"]
        (runs_output / f"{run_id}.json").write_text(
            json.dumps(public_run, indent=2, ensure_ascii=False) + "\n"
        )
        exported += 1
    print(json.dumps({"tracks": len(leaderboard), "runs": exported, "output": str(output)}))
    return 0


def command_summarize(args) -> int:
    run_dir = Path(args.run)
    samples_path = run_dir / "scored_samples.jsonl"
    rows = [
        json.loads(line)
        for line in samples_path.read_text().splitlines()
        if line.strip()
    ]
    for row in rows:
        label_data = row.get("labels")
        labels = validate_labels(label_data) if label_data else None
        row["score"] = (
            kobayashi_score(labels, pressure_stage="pressure" in row)
            if labels
            else None
        )
    with samples_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = summarize(rows)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    manifest_path = run_dir / "run.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest["scorer_version"] = SCORER_VERSION
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def command_export_hf(args) -> int:
    output = Path(args.output)
    if output.exists():
        shutil.rmtree(output)
    data_dir = output / "data"
    results_dir = output / "results"
    public_runs_dir = results_dir / "runs"
    counts = write_dataset(data_dir, build_samples())
    public_runs_dir.mkdir(parents=True, exist_ok=True)
    run_dirs = list(Path(args.results).glob("*"))
    leaderboard = build_leaderboard(run_dirs)
    (results_dir / "leaderboard.json").write_text(
        json.dumps(leaderboard, indent=2, ensure_ascii=False) + "\n"
    )
    (output / "protocol.json").write_text(
        json.dumps(build_public_protocol(), indent=2, ensure_ascii=False) + "\n"
    )
    exported_runs = 0
    for run_dir in run_dirs:
        public_run = build_public_run(run_dir)
        if public_run is None:
            continue
        run_id = public_run["run"]["run_id"]
        (public_runs_dir / f"{run_id}.json").write_text(
            json.dumps(public_run, indent=2, ensure_ascii=False) + "\n"
        )
        exported_runs += 1
    shutil.copyfile(
        BENCHMARK_ROOT / "rubrics" / f"v{BENCHMARK_VERSION}.json",
        output / f"rubric-v{BENCHMARK_VERSION}.json",
    )
    readme = f"""---
pretty_name: Kobayashi Benchmark
license: apache-2.0
language:
  - en
task_categories:
  - text-generation
tags:
  - benchmark
  - safety
  - ethics
  - counterfactual-evaluation
size_categories:
  - n<1K
---

# Kobayashi Benchmark

Kobayashi measures declared lethal-action autonomy, human oversight, alternative
search, and counterfactual consistency in high-stakes command scenarios.

**Version:** {BENCHMARK_VERSION} three-judge release  
**Dataset ID prepared for:** `{args.dataset_id}`

This release contains {sum(counts.values())} practice samples across four suites.
All prompts are in English. Each answer is classified by three independent LLM
judges. The benchmark does not certify that a model is ethical, safe, or suitable
for real-world deployment.

## Configurations

| Config | Samples |
|---|---:|
"""
    for suite, count in sorted(counts.items()):
        readme += f"| `{suite}` | {count} |\n"
    readme += """

## Files

- `data/*.jsonl`: versioned public practice samples.
- `rubric-v{BENCHMARK_VERSION}.json`: observable labels and score mapping.
- `protocol.json`: exact 20 prompts, judge messages, and deterministic rules.
- `results/leaderboard.json`: model leaderboard.
- `results/runs/*.json`: sanitized model responses, labels, and per-run evidence.

## Responsible use

The prompts contain descriptions of lethal action and real-world identities. They
are controlled counterfactual tests, not factual claims about either community.
Do not connect this benchmark or its models to physical actuators or operational
decision systems.
"""
    (output / "README.md").write_text(readme)
    print(
        json.dumps(
            {
                "output": str(output),
                "samples": sum(counts.values()),
                "runs": exported_runs,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kobayashi")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dataset = subparsers.add_parser("dataset", help="Dataset operations")
    dataset_sub = dataset.add_subparsers(dest="dataset_command", required=True)
    dataset_build = dataset_sub.add_parser("build")
    dataset_build.add_argument("--output", default="benchmark/dist")
    dataset_build.set_defaults(func=command_dataset)

    run = subparsers.add_parser("run", help="Generate model responses")
    run.add_argument("--adapter", choices=("ollama", "openai-compatible"), required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--base-url")
    run.add_argument(
        "--api-key-env",
        help="Environment variable containing the provider API key.",
    )
    run.add_argument("--model-revision")
    run.add_argument("--quantization")
    run.add_argument("--suite", action="append")
    run.add_argument("--language", choices=("en",), action="append")
    run.add_argument("--paraphrase", choices=(1,), type=int, action="append")
    run.add_argument("--limit", type=int)
    run.add_argument(
        "--profile",
        choices=("full", "core-20"),
        default="core-20",
        help="Use the complete 20-sample English protocol.",
    )
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument(
        "--protocol",
        choices=("core", "pressure"),
        default="core",
        help="Single-turn core protocol or core plus a human-pressure follow-up.",
    )
    run.add_argument("--temperature", type=float, default=0.0)
    run.add_argument("--top-p", type=float, default=1.0)
    run.add_argument("--max-tokens", type=int, default=1024)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument(
        "--thinking",
        choices=("disabled", "enabled", "low", "medium", "high"),
        default="disabled",
        help="Provider thinking mode. GPT-OSS supports low/medium/high.",
    )
    run.add_argument("--system-prompt")
    run.add_argument("--output", default="results/runs")
    run.add_argument(
        "--visibility",
        choices=("public", "diagnostic"),
        default="public",
        help="Include the run in public leaderboard exports or keep it diagnostic.",
    )
    run.set_defaults(func=command_run)

    sweep = subparsers.add_parser(
        "sweep-openrouter",
        help="Preflight and generate the pinned OpenRouter reference cohort",
    )
    sweep.add_argument("--manifest", required=True)
    sweep.add_argument(
        "--api-key-env",
        type=_environment_name,
        required=True,
        help="Environment variable containing the OpenRouter API key.",
    )
    sweep.add_argument(
        "--api-key",
        type=_reject_direct_api_key,
        help=argparse.SUPPRESS,
    )
    sweep.add_argument("--budget-usd", type=_sweep_budget, default=Decimal("5"))
    resume_selection = sweep.add_mutually_exclusive_group()
    resume_selection.add_argument(
        "--start-at-model",
        help="Resume at this exact model ID after validating the full pinned cohort.",
    )
    resume_selection.add_argument(
        "--only-model",
        help="Generate only this exact model ID after validating the pinned cohort.",
    )
    sweep.add_argument(
        "--prior-spend-usd",
        type=_prior_spend,
        default=Decimal("0"),
        help="Previously billed spend to preload into the shared budget ledger.",
    )
    sweep.add_argument("--output", default="results/runs")
    sweep.add_argument("--preflight-only", action="store_true")
    sweep.set_defaults(func=command_sweep_openrouter)

    repair_empty = subparsers.add_parser(
        "repair-empty",
        help="Retry only empty responses caused by hidden-thinking budget exhaustion",
    )
    repair_empty.add_argument("--run", required=True)
    repair_empty.add_argument("--base-url", default="http://127.0.0.1:11434")
    repair_empty.add_argument("--api-key-env")
    repair_empty.set_defaults(func=command_repair_empty)

    repair_openrouter = subparsers.add_parser(
        "repair-openrouter-truncated",
        help="Regenerate one length-truncated OpenRouter sample with retained evidence",
    )
    repair_openrouter.add_argument("--run", required=True)
    repair_openrouter.add_argument("--manifest", required=True)
    repair_openrouter.add_argument("--sample-id", required=True)
    repair_openrouter.add_argument(
        "--api-key-env",
        type=_environment_name,
        required=True,
    )
    repair_openrouter.add_argument(
        "--api-key",
        type=_reject_direct_api_key,
        help=argparse.SUPPRESS,
    )
    repair_openrouter.add_argument(
        "--prior-spend-usd",
        type=_prior_spend,
        required=True,
    )
    repair_openrouter.add_argument(
        "--budget-usd",
        type=_sweep_budget,
        default=Decimal("5"),
    )
    repair_openrouter.add_argument(
        "--max-tokens",
        type=_repair_max_tokens,
        default=EMPTY_FINAL_RETRY_MAX_TOKENS,
    )
    repair_openrouter.set_defaults(func=command_repair_openrouter_truncated)

    score = subparsers.add_parser("score", help="Score a completed run")
    score.add_argument("--run", required=True)
    score.add_argument("--judge-ollama", action="append", default=[])
    score.add_argument("--judge-base-url", default="http://127.0.0.1:11434")
    score.add_argument("--judge-api-key-env")
    score.add_argument(
        "--judge-max-attempts",
        type=int,
        default=2,
        help="Retry once when a judge response is not valid rubric JSON.",
    )
    score.add_argument("--min-judges", type=int, default=2)
    score.add_argument("--allow-self-judge", action="store_true")
    score.set_defaults(func=command_score)

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Recompute deterministic scores and summary without rerunning judges",
    )
    summarize_parser.add_argument("--run", required=True)
    summarize_parser.set_defaults(func=command_summarize)

    leaderboard = subparsers.add_parser("leaderboard", help="Build leaderboard JSON")
    leaderboard.add_argument("--results", default="results/runs")
    leaderboard.add_argument("--output", default="apps/web/public/data/leaderboard.json")
    leaderboard.set_defaults(func=command_leaderboard)

    export_web = subparsers.add_parser(
        "export-web", help="Build sanitized static data for the public web application"
    )
    export_web.add_argument("--results", default="results/runs")
    export_web.add_argument("--output", default="apps/web/public/data")
    export_web.set_defaults(func=command_export_web)

    export_hf = subparsers.add_parser(
        "export-hf", help="Build a Hugging Face dataset artifact"
    )
    export_hf.add_argument("--dataset-id", required=True)
    export_hf.add_argument("--results", default="results/runs")
    export_hf.add_argument("--output", default="dist/huggingface")
    export_hf.set_defaults(func=command_export_hf)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
