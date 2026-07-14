export type SuiteSummary = {
  score: number;
  samples: number;
  stderr: number;
};

export type LeaderboardEntry = {
  track_id: string;
  run_id: string;
  language: "es" | "en";
  model: string;
  provider: string;
  benchmark_version: string;
  scorer_version: string | null;
  verification: "verified" | "reproducible-community" | "local-provisional" | "self-reported";
  protocol: "core" | "pressure";
  created_at: string;
  kobayashi_score: number | null;
  partial_kobayashi_score: number | null;
  coverage_status: "complete" | "insufficient";
  suite_coverage: number;
  score_ci_95: [number, number] | null;
  samples_total: number;
  samples_scored: number;
  invalid_evasive_rate: number;
  autonomous_lethal_action_rate: number;
  human_escalation_rate: number;
  non_lethal_alternative_rate: number;
  counterfactual_consistency: number | null;
  mean_judge_agreement: number | null;
  human_review_rate: number;
  generation_truncation_rate: number;
  mean_latency_ms: number | null;
  mean_completion_tokens: number | null;
  by_suite: Record<string, SuiteSummary>;
};

export type PublicRunSample = {
  sample_id: string;
  language: "es" | "en";
  suite: string;
  identity_direction: "neutral" | "a_to_b" | "b_to_a";
  paraphrase: number;
  prompt: string;
  response: string;
  generation: {
    latency_ms: number | null;
    prompt_tokens: number | null;
    completion_tokens: number | null;
    error: string | null;
    done_reason: string | null;
  };
  labels: Record<string, string | number> | null;
  score: number | null;
  judge_agreement: number | null;
  judge_success_count: number | null;
  needs_human_review: boolean;
  pressure?: { prompt: string; response: string };
};

export type PublicRun = {
  schema_version: 1;
  run: {
    run_id: string;
    model: string;
    provider: string;
    benchmark_version: string;
    verification: string;
    [key: string]: unknown;
  };
  summary: { schema_version: 2; tracks: Record<string, unknown> };
  samples: PublicRunSample[];
};
