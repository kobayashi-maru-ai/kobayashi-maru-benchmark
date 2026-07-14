# Kobayashi Benchmark

[![CI](https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark/actions/workflows/ci.yml)
[![Dataset](https://img.shields.io/badge/Hugging%20Face-dataset-FFD21E)](https://huggingface.co/datasets/ericrisco/kobayashi-benchmark)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

Kobayashi is an open, versioned benchmark for measuring how language models
respond to high-stakes scenarios involving potentially lethal action. It
measures declared behavior under a prompt; it does **not** certify that a model
is ethical, safe, or suitable for deployment in a real decision system.

The project contains:

- A bilingual, counterfactual scenario dataset.
- A reproducible CLI for local and API-served models.
- Auditable per-sample traces and a versioned scoring rubric.
- Hugging Face-compatible benchmark metadata.
- A public methodology and leaderboard web application.

## Quick start

```bash
uvx --from git+https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark.git@v0.1.0 \
  kobayashi run --adapter ollama --model ministral-3:latest --profile pilot-12
uvx --from git+https://github.com/kobayashi-maru-ai/kobayashi-maru-benchmark.git@v0.1.0 \
  kobayashi score --run results/runs/<run-id> \
  --judge-ollama gpt-oss:20b \
  --judge-ollama gemma3:12b \
  --judge-ollama gemma4:e4b
```

This path requires only [uv](https://docs.astral.sh/uv/) and a running Ollama
service; the tagged CLI includes its versioned prompts and rubric. Contributors
can instead clone the repository, run `uv sync --frozen`, and prefix commands
with `uv run`.

The first release is `0.1.0`, a calibration release. Its scores are provisional
until the scorer has been validated against the human-labelled calibration set.
The calibration dataset and provisional results are published at
[Hugging Face](https://huggingface.co/datasets/ericrisco/kobayashi-benchmark).

## Safety boundary

Kobayashi evaluates text responses to fictional scenarios. It never connects a
model to weapons, vehicles, police systems, targeting systems, or other physical
actuators. Results must be reported with their benchmark, runner, model, and
scorer versions.
