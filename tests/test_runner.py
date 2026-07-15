import json
import tempfile
import unittest
from pathlib import Path

from kobayashi_benchmark.dataset import build_samples, pilot_samples
from kobayashi_benchmark.models import GenerationConfig, GenerationResult
from kobayashi_benchmark.runner import create_run


class FakeAdapter:
    provider = "fake"
    model = "fake-model"

    def __init__(self):
        self.prompts = []

    def generate(self, prompt, config, system_prompt=None):
        self.prompts.append(prompt)
        return GenerationResult(text="I reject lethal action.", latency_ms=1)


class RunnerTests(unittest.TestCase):
    def test_pressure_protocol_records_both_turns(self):
        adapter = FakeAdapter()
        sample = pilot_samples(build_samples())[:1]
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = create_run(
                adapter,
                sample,
                GenerationConfig(max_tokens=10),
                Path(temp_dir),
                protocol="pressure",
            )
            row = json.loads((run_dir / "samples.jsonl").read_text().strip())
            manifest = json.loads((run_dir / "run.json").read_text())
        self.assertIn("pressure", row)
        self.assertEqual(len(adapter.prompts), 2)
        self.assertEqual(manifest["protocol"], "pressure")

    def test_empty_final_from_hidden_thinking_is_retried_with_more_headroom(self):
        class HiddenThinkingAdapter(FakeAdapter):
            def __init__(self):
                super().__init__()
                self.max_tokens = []

            def generate(self, prompt, config, system_prompt=None):
                self.prompts.append(prompt)
                self.max_tokens.append(config.max_tokens)
                if len(self.prompts) == 1:
                    return GenerationResult(
                        text="",
                        latency_ms=1,
                        error=(
                            "empty final response "
                            "(thinking exhausted the generation budget)"
                        ),
                        provider_metadata={"thinking_chars": 2000},
                    )
                return GenerationResult(text="Final answer.", latency_ms=1)

        adapter = HiddenThinkingAdapter()
        sample = pilot_samples(build_samples())[:1]
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = create_run(
                adapter,
                sample,
                GenerationConfig(max_tokens=1024),
                Path(temp_dir),
            )
            row = json.loads((run_dir / "samples.jsonl").read_text().strip())

        self.assertEqual(adapter.max_tokens, [1024, 4096])
        self.assertEqual(row["generation"]["text"], "Final answer.")
        self.assertEqual(len(row["generation_repair"]["attempts"]), 2)

    def test_gpt_oss_gets_one_final_low_thinking_fallback(self):
        class GptOssAdapter(FakeAdapter):
            model = "gpt-oss:20b"

            def __init__(self):
                super().__init__()
                self.configs = []

            def generate(self, prompt, config, system_prompt=None):
                self.prompts.append(prompt)
                self.configs.append(config)
                if len(self.prompts) < 3:
                    return GenerationResult(
                        text="",
                        latency_ms=1,
                        error=(
                            "empty final response "
                            "(thinking exhausted the generation budget)"
                        ),
                    )
                return GenerationResult(text="Final answer.", latency_ms=1)

        adapter = GptOssAdapter()
        sample = pilot_samples(build_samples())[:1]
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = create_run(
                adapter,
                sample,
                GenerationConfig(max_tokens=1024, thinking="disabled"),
                Path(temp_dir),
            )
            row = json.loads((run_dir / "samples.jsonl").read_text().strip())

        self.assertEqual(
            [(config.max_tokens, config.thinking) for config in adapter.configs],
            [(1024, "disabled"), (4096, "disabled"), (4096, "low")],
        )
        self.assertEqual(row["generation"]["text"], "Final answer.")
        self.assertEqual(len(row["generation_repair"]["attempts"]), 3)


if __name__ == "__main__":
    unittest.main()
