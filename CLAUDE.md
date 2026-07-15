# CLAUDE.md — kobayashi-maru-benchmark

This file is the root instruction source for agents working in this workspace.

## Sistema de diseño (OBLIGATORIO)

Todo trabajo de interfaz DEBE seguir [`DESIGN.md`](DESIGN.md), el contrato visual
canónico del proyecto.

- Canvas `#090A0B`, superficies `#111315`/`#17191C` y texto `#EDEDE8`.
- Amarillo `#F4C430` para navegación de investigación; rojo `#EF5B4D` para
  provisional/advertencia; verde `#54C98A` únicamente para verificado.
- Space Grotesk para display y cuerpo; IBM Plex Mono sólo para evidencia y datos.
- Objetivos interactivos de al menos 44px; navegación cápsula, tablas y reglas planas.
- Cero sombras decorativas, glow, glassmorphism o tarjetas genéricas.
- Contenido 1232px; columna editorial 752px; evidencia puede abrirse a 1088px.
- ES y EN siempre separados; provisional, cobertura y revisión humana explícitos.
- Responsive móvil conserva navegación, caveats y métricas críticas; no las oculta.
- Foco visible `#FFDA5A`, contraste WCAG AA y `prefers-reduced-motion` obligatorios.

**Don'ts críticos:** cumplir `DESIGN.md §7`, incluida la prohibición de copiar
logos o código de ARC Prize, copiar Star Trek, usar glow o presentar scores
provisionales como verificados.

If a user request contradicts `DESIGN.md`, flag it and propose the aligned version
before implementing. The document is the contract.

## What this project is

An open benchmark and public leaderboard for evaluating how language models
describe decisions about lethal action, human oversight, and counterfactual
identity changes in fictional high-stakes scenarios. It includes a Python CLI,
versioned dataset and scorer, auditable result traces, and a Next.js web app.

## Workspace map

| Path | Role |
|------|------|
| `src/kobayashi_benchmark/` | Python dataset builder, model adapters, runner, scorer, metrics, and CLI. |
| `benchmark/` | Versioned scenario kernels, rubrics, schemas, and Hugging Face metadata. |
| `apps/web/` | Next.js App Router site and leaderboard API. |
| `results/runs/` | Auditable local model generations, scorer traces, and summaries. |
| `tests/` | Dataset, scoring, reporting, and runner invariants. |

The workspace root is a Git repository and pnpm workspace. Python packaging is
managed by uv; the web package is managed by pnpm.

## Working rules

- Before editing, run `git status --short`; the user may have in-flight changes.
- Ignore generated outputs unless asked: `node_modules/`, `.next/`, `.venv/`,
  `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.dart_tool/`, `build/`,
  `dist/`, and `__pycache__/`.
- Never publish secrets. API keys, SSH keys, service accounts, and tokens are
  sensitive.
- Keep future subproject boundaries clean; do not mix dependencies or stacks.

## Main commands

```bash
uv sync
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/kobayashi dataset build --output benchmark/dist
.venv/bin/kobayashi run --adapter ollama --model <model> --profile pilot-12
.venv/bin/kobayashi score --run <run-dir> --judge-ollama <judge>
pnpm install
pnpm web:dev
pnpm web:typecheck
pnpm web:lint
pnpm web:build
```
