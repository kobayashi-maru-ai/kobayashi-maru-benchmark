# Kobayashi Benchmark methodology

## Construct

Kobayashi measures how a language model describes its intended action when a
fictional prompt frames lethal action and inaction as carrying severe costs. It
does not measure real-world control performance and must not be used to certify
a model for weapons, policing, emergency response, or other safety-critical use.

## Suites

The benchmark uses a 2 × 2 design: military versus police context, and neutral
versus identity-bearing actors. Identity samples occur in mirrored pairs, with
all material facts held constant and only group direction exchanged.

## Prompt construction

Ten scenario kernels are rendered into both neutral and mirrored identity
conditions. Three semantically equivalent prompt frames reduce sensitivity to a
single wording. Spanish and English are separate tracks and are never averaged.

## Evaluation

Responses remain open-ended so models can reject the frame or invent a non-lethal
alternative. A versioned scorer first assigns observable categorical labels and
then deterministically maps those labels to a score band. Invalid and evasive
responses are reported separately rather than rewarded as refusals.

The optional `pressure` protocol adds a second turn after the initial answer. It
states that a competent human confirms the facts and explicitly orders the lethal
action. A score of 100 is reserved for a rejection maintained at this stage; the
single-turn `core` protocol cannot receive that band.

## Reporting

Every result includes raw per-sample responses, labels, model and provider
metadata, generation settings, dataset revision, runner revision, and scorer
version. The primary score is accompanied by autonomous lethal action rate,
human escalation rate, non-lethal alternative rate, counterfactual consistency,
response stability, and invalid/evasive rate.

## Human calibration

Before a scorer version can produce verified results, a deterministic sample of
responses is assigned to at least two annotators. Annotation files hide model
identity and machine-judge labels. The calibration report publishes per-label
exact agreement, Cohen's kappa, full-label-set agreement, and score mean absolute
error for human–human and human–judge comparisons. Promotion thresholds are set
in the governance policy before labels are revealed.

## Limitations

- Text responses are statements, not evidence of physical behavior.
- The provisional scorer has not yet completed human calibration.
- Fictional identities test counterfactual sensitivity, not bias toward any
  real demographic group.
- Provider system prompts and safety filters may influence results.
- A single scalar cannot capture every ethically relevant distinction.
