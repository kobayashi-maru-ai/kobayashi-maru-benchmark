import protocolData from "../../public/data/protocol.json";

export type ProtocolPrompt = {
  id: string;
  language: "en";
  suite: string;
  identity_direction: "israeli_to_palestinian" | "palestinian_to_israeli";
  prompt: string;
};

export type ScoreRule = {
  priority: number;
  score: number | string | null;
  when: string;
};

export type PublicProtocol = {
  schema_version: number;
  benchmark_version: string;
  profile: string;
  reference_generation_config: Record<string, string | number>;
  generation_repair_policy: {
    trigger: string;
    max_attempts: number;
    retry_max_tokens: number;
    final_attempt_adjustment: string;
    audit: string;
  };
  prompts: ProtocolPrompt[];
  judge: {
    panel_policy: {
      primary_models: string[];
      self_judge_replacement: string;
      rule: string;
    };
    system_prompt: string;
    prompt_template: string;
    generation_config: Record<string, string | number>;
    allowed_labels: Record<string, string[]>;
    max_attempts: number;
    retry_policy: string;
    retry_instruction: string;
  };
  score_rules: ScoreRule[];
  aggregation: Record<string, string | number>;
};

export function getProtocol(): PublicProtocol {
  return protocolData as PublicProtocol;
}
