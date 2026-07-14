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


if __name__ == "__main__":
    unittest.main()
