# Hugging Face publication

## Community dataset release

Build the upload-ready dataset artifact:

```bash
kobayashi export-hf \
  --dataset-id <namespace>/kobayashi-benchmark \
  --output dist/huggingface
```

Upload `dist/huggingface/` to a Hugging Face dataset repository. This publishes
the practice set, rubric, dataset card, and provisional reference results.

The `0.1.0` calibration release is published at
<https://huggingface.co/datasets/ericrisco/kobayashi-benchmark>. Its first Hub
commit is `c04b80e5ebe9018006aea94904339e23d3318fd6`.

## Official benchmark registration

Hugging Face official benchmark registration requires an accepted evaluation
framework identifier in `eval.yaml` and allow-list approval. Kobayashi's scalar
scorer is custom and must not be represented as a built-in Inspect scorer until
that integration is implemented and validated. Until then, publish it as a
community dataset and leaderboard Space rather than claiming official status.

## Result provenance

Each public score must link to `run.json`, `scored_samples.jsonl`, and
`summary.json`. The web labels current runs `local-provisional`; do not upgrade
them to `verified` without a maintainer-controlled rerun and human-calibrated
scorer.
