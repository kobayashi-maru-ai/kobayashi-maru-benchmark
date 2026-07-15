import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from kobayashi_benchmark.cli import (
    _adapter,
    _is_official_ollama_cloud,
    command_export_hf,
    command_export_web,
)


class OllamaCredentialRoutingTests(unittest.TestCase):
    def test_only_exact_official_origin_is_cloud(self):
        self.assertTrue(_is_official_ollama_cloud("https://ollama.com"))
        self.assertTrue(_is_official_ollama_cloud("https://ollama.com:443/"))
        self.assertFalse(_is_official_ollama_cloud("https://ollama.com.evil.example"))
        self.assertFalse(_is_official_ollama_cloud("http://ollama.com"))
        self.assertFalse(_is_official_ollama_cloud("https://ollama.com/api"))

    @patch.dict("os.environ", {"OLLAMA_API_KEY": "cloud-secret"})
    def test_default_cloud_key_is_not_sent_to_custom_endpoint(self):
        args = Namespace(
            adapter="ollama",
            model="model-a",
            base_url="https://ollama.com.evil.example",
            api_key_env=None,
        )

        adapter = _adapter(args)

        self.assertIsNone(adapter.api_key)
        self.assertEqual(adapter.provider, "ollama")

    @patch.dict("os.environ", {"CUSTOM_OLLAMA_KEY": "custom-secret"})
    def test_custom_endpoint_key_requires_explicit_environment_name(self):
        args = Namespace(
            adapter="ollama",
            model="model-a",
            base_url="https://models.example",
            api_key_env="CUSTOM_OLLAMA_KEY",
        )

        adapter = _adapter(args)

        self.assertEqual(adapter.api_key, "custom-secret")


class ExportWebTests(unittest.TestCase):
    def test_export_removes_stale_public_run_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            results = root / "results"
            output = root / "public"
            results.mkdir()
            stale_runs = output / "runs"
            stale_runs.mkdir(parents=True)
            (stale_runs / "old-run.json").write_text("{}")

            command_export_web(Namespace(results=str(results), output=str(output)))

            self.assertFalse((stale_runs / "old-run.json").exists())
            self.assertTrue((output / "protocol.json").exists())

    def test_hugging_face_export_removes_stale_files_and_includes_protocol(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            results = root / "results"
            output = root / "huggingface"
            results.mkdir()
            output.mkdir()
            (output / "stale.json").write_text("{}")

            command_export_hf(
                Namespace(
                    results=str(results),
                    output=str(output),
                    dataset_id="example/kobayashi",
                )
            )

            self.assertFalse((output / "stale.json").exists())
            self.assertTrue((output / "protocol.json").exists())
            self.assertTrue((output / "results" / "leaderboard.json").exists())


if __name__ == "__main__":
    unittest.main()
