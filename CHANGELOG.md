# Changelog

All notable benchmark, runner, scorer, and publication changes are recorded here.

## 0.2.0 — 2026-07-14

- Replaced the local reference pilots with one fixed `pilot-12` run for every
  model exposed by the authenticated Ollama Cloud catalogue.
- Added authenticated Ollama Cloud generation and three-model judging without
  allowing a model to judge itself.
- Added one retry for invalid judge JSON, larger reasoning-model output
  headroom, diagnostic validation feedback, protocol-aware judge caches, and
  explicit operational label rules.
- Added a bounded, per-sample empty-final repair that preserves every attempt
  and provider-specific configuration without duplicating model runs.
- Published every evaluated prompt, judge instruction, generation setting,
  retry rule, aggregation rule, and score rule in the README and website.
- Rebuilt the website as a scientific research dossier and added a dedicated
  protocol explorer and reproducibility guide.
- Removed the obsolete operational-tooling and generated-wiki directories.

## 0.1.0 — 2026-07-14

- Added 180 bilingual practice prompts across four military/police and
  neutral/identity suites.
- Added mirrored fictional-identity counterfactuals and three paraphrases.
- Added Ollama and OpenAI-compatible runners with core and pressure protocols.
- Added an observable-label scorer, three-judge consensus policy, immutable
  traces, resumable judge caches, and human-review flags.
- Added strictly separate Spanish and English tracks.
- Added blind two-annotator calibration packs and precommitted promotion gates.
- Published three 12-sample local provisional model pilots.
- Published the community dataset on Hugging Face.
