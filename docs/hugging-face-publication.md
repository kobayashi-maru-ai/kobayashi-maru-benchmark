# Hugging Face publication

## Community dataset release

Build the upload-ready dataset artifact:

```bash
kobayashi export-hf \
  --dataset-id <namespace>/kobayashi-benchmark \
  --output dist/huggingface
```

Upload `dist/huggingface/` to a Hugging Face dataset repository. This publishes
the practice set, rubric, complete protocol disclosure, leaderboard, and
sanitized per-run evidence for every provisional reference result.

The `0.2.0` Ollama Cloud reference release is published at
<https://huggingface.co/datasets/ericrisco/kobayashi-benchmark>. Its Hub commit
is `afeb66c73ce3789cc35d4723e62ea5360d76aae8`.

## Official benchmark registration

Hugging Face official benchmark registration requires an accepted evaluation
framework identifier in `eval.yaml` and allow-list approval. Kobayashi's scalar
scorer is custom and must not be represented as a built-in Inspect scorer until
that integration is implemented and validated. Until then, publish it as a
community dataset and leaderboard Space rather than claiming official status.

## Result provenance

Each public score must retain its run manifest, model response, consensus labels,
summary, and judge-attempt metadata. The web labels current Ollama Cloud runs
`provisional`; do not upgrade them to `verified` without a
maintainer-controlled rerun and human-calibrated scorer.
