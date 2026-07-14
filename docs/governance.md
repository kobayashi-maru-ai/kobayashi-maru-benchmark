# Benchmark governance

## Versioning

Dataset, runner, rubric, and judge configuration are versioned independently.
Changing a prompt, label definition, score mapping, or judge configuration
requires a version bump and re-evaluation of reference models.

## Result tiers

1. **Verified** — executed by benchmark maintainers with a human-calibrated scorer.
2. **Reproducible community** — complete traces and revisions are published.
3. **Local provisional** — maintainer pilot without completed human calibration.
4. **Self-reported** — aggregate values without complete auditable traces.

## Scorer promotion gates

The following thresholds are fixed before human labels are revealed. A scorer
version can move results from local provisional to verified only when:

- At least 24 responses have two independent blind annotations.
- Human–human raw agreement is at least 0.80 and Cohen's kappa at least 0.60
  for every categorical field.
- For `lethal_commitment` and `final_action`, human–human raw agreement is at
  least 0.90 and Cohen's kappa at least 0.75.
- Human–judge raw agreement is at least 0.80 for every field.
- Human–judge score mean absolute error is no greater than 10 points.
- Every disagreement affecting a public score has been adjudicated by a third
  human annotator.

## Contributions

Scenario contributions require a mirrored counterfactual, rationale, content
review, and tests proving all non-target facts remain equivalent. Real-world
protected identities require additional domain and ethics review before entry
into an official set.
