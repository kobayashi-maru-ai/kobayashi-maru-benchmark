# Kobayashi Benchmark

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
uv sync
uv run kobayashi dataset build --output benchmark/dist
uv run kobayashi run --adapter ollama --model ministral-3:latest --profile pilot-12
uv run kobayashi score --run results/runs/<run-id> \
  --judge-ollama gpt-oss:20b \
  --judge-ollama gemma3:12b \
  --judge-ollama gemma4:e4b
uv run kobayashi export-web
```

The first release is `0.1.0`, a calibration release. Its scores are provisional
until the scorer has been validated against the human-labelled calibration set.
The calibration dataset and provisional results are published at
[Hugging Face](https://huggingface.co/datasets/ericrisco/kobayashi-benchmark).

## Safety boundary

Kobayashi evaluates text responses to fictional scenarios. It never connects a
model to weapons, vehicles, police systems, targeting systems, or other physical
actuators. Results must be reported with their benchmark, runner, model, and
scorer versions.
