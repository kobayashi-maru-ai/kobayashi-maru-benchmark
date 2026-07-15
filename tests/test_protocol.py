import unittest
from pathlib import Path

from kobayashi_benchmark.dataset import build_samples, pilot_samples
from kobayashi_benchmark.protocol import build_public_protocol
from kobayashi_benchmark.scoring import (
    JUDGE_RETRY_INSTRUCTION,
    JUDGE_SYSTEM,
    judge_prompt,
)


class PublicProtocolTests(unittest.TestCase):
    def test_public_protocol_contains_the_exact_pilot_prompts(self):
        protocol = build_public_protocol()
        expected = [sample.prompt for sample in pilot_samples(build_samples())]

        self.assertEqual([item["prompt"] for item in protocol["prompts"]], expected)
        self.assertEqual(len(protocol["prompts"]), 12)

    def test_public_protocol_discloses_json_retry_policy(self):
        judge = build_public_protocol()["judge"]

        self.assertEqual(judge["max_attempts"], 2)
        self.assertEqual(judge["generation_config"]["max_tokens"], 4096)
        self.assertIn("Retry once", judge["retry_policy"])

    def test_public_protocol_discloses_non_self_judging_panel(self):
        policy = build_public_protocol()["judge"]["panel_policy"]

        self.assertEqual(len(policy["primary_models"]), 3)
        self.assertNotIn(policy["self_judge_replacement"], policy["primary_models"])
        self.assertIn("never allow self-judging", policy["rule"])

    def test_public_protocol_discloses_empty_final_repair(self):
        policy = build_public_protocol()["generation_repair_policy"]

        self.assertEqual(policy["max_attempts"], 3)
        self.assertEqual(policy["retry_max_tokens"], 4096)

    def test_public_protocol_discloses_track_aggregation(self):
        aggregation = build_public_protocol()["aggregation"]

        self.assertIn("four suite means", aggregation["track_score"])
        self.assertIn("100 - absolute", aggregation["counterfactual_consistency"])
        self.assertIn("2,000-resample", aggregation["confidence_interval"])

    def test_readme_contains_every_reference_prompt_verbatim(self):
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()

        for item in build_public_protocol()["prompts"]:
            self.assertIn(item["prompt"], readme)

        self.assertIn(JUDGE_SYSTEM, readme)
        self.assertIn(judge_prompt("{{QUESTION}}", "{{ASSISTANT_RESPONSE}}"), readme)
        self.assertIn(JUDGE_RETRY_INSTRUCTION, readme)


if __name__ == "__main__":
    unittest.main()
