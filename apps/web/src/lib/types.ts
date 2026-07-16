export type SuiteSummary = {
  score: number;
  samples: number;
  stderr: number;
};

export type ReleaseClass =
  | "closed_proprietary"
  | "open_weights"
  | "open_source";

export type OriginRegion =
  | "china"
  | "united_states"
  | "europe"
  | "other";

export type ResultCohort = "reference" | "community";

export type LeaderboardEntry = {
  track_id: string;
  run_id: string;
  language: "en";
  model: string;
  result_cohort: ResultCohort;
  organization: string;
  release_class: ReleaseClass;
  origin_region: OriginRegion;
  origin_country: string;
  taxonomy_source_url: string;
  taxonomy_source_label: string;
  taxonomy_classified_at: string;
  taxonomy_note: string;
  benchmark_version: string;
  scorer_version: string | null;
  verification:
    | "three-judge-evaluated"
    | "three-judge-pending"
    | "self-reported";
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
  generation_truncation_rate: number;
  mean_latency_ms: number | null;
  mean_completion_tokens: number | null;
  by_suite: Record<string, SuiteSummary>;
};

export type PublicRunSample = {
  sample_id: string;
  language: "en";
  suite: string;
  identity_direction: "israeli_to_palestinian" | "palestinian_to_israeli";
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
  generation_repair?: {
    reason: string;
    max_attempts: number;
    repair_config: Record<string, string | number>;
    attempt_configs: Array<Record<string, string | number>>;
    attempts: Array<{
      latency_ms: number | null;
      completion_tokens: number | null;
      error: string | null;
      done_reason: string | null;
      thinking_chars: number | null;
    }>;
  };
  pressure?: { prompt: string; response: string };
};

export type PublicRun = {
  schema_version: 1;
  run: {
    run_id: string;
    model: string;
    benchmark_version: string;
    verification: string;
    [key: string]: unknown;
  };
  summary: {
    schema_version: 2;
    tracks: Record<
      string,
      {
        kobayashi_score: number | null;
        partial_kobayashi_score: number | null;
        coverage_status: "complete" | "insufficient";
        samples_total: number;
        samples_scored: number;
        mean_judge_agreement: number | null;
        autonomous_lethal_action_rate: number;
        counterfactual_consistency: number | null;
      }
    >;
  };
  samples: PublicRunSample[];
};
