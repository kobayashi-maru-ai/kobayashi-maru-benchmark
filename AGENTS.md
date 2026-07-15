# AGENTS.md — kobayashi-maru-benchmark

> This is the first read for Codex, Cursor, Aider, and other coding agents.
> Claude Code should also read `CLAUDE.md`.

## Workspace

The workspace root is a Git repository and pnpm workspace. The benchmark core
is a Python package managed by uv; the public site is a Next.js App Router app.

## Quick map

| Path | Role |
|------|------|
| `src/kobayashi_benchmark/` | Dataset, runner, model adapters, scorer, metrics, and CLI. |
| `benchmark/` | Versioned scenario kernels, rubrics, schemas, and publication metadata. |
| `apps/web/` | Next.js public site and leaderboard API. |
| `results/runs/` | Auditable local evaluation artifacts. |
| `tests/` | Benchmark invariants and regression tests. |

## Minimum rules

1. Before editing, run `git status --short` and preserve in-flight changes.
2. Do not commit without asking.
3. Do not touch generated outputs such as `node_modules/`, `.venv/`, `.next/`,
   `__pycache__/`, `.dart_tool/`, `build/`, or `dist/`.

## Per-subproject commands

```bash
# Benchmark core
uv sync
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/kobayashi --help

# Web
pnpm install
pnpm web:typecheck
pnpm web:lint
pnpm web:build
```

## Differences from `CLAUDE.md`

None. Both files currently express the same workspace constraints.
