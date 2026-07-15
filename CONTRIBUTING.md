# Contributing

## Development setup

```bash
uv sync --group dev
pnpm install --frozen-lockfile
uv run pytest
uv run ruff check .
pnpm web:typecheck
pnpm web:lint
```

## Scenario changes

Do not edit a published benchmark version. Create a new version and include
English mirrored counterfactual cases, dataset-invariant tests, a rubric revision,
and a changelog entry. Material facts must remain identical across identity swaps.

## Result submissions

A result must include its run manifest, raw responses, consensus labels,
summary, dataset digest, model revision where available, generation settings,
judge panel, and scorer policy. Self-judging panels are rejected. Aggregate-only
submissions are displayed as self-reported and cannot become verified.

## Pull requests

Keep changes focused, explain methodology changes explicitly, and run every
local check above. Never commit credentials or private endpoint configuration.
