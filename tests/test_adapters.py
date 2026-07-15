import unittest
from unittest.mock import patch

from kobayashi_benchmark.adapters import OllamaAdapter
from kobayashi_benchmark.models import GenerationConfig


class OllamaAdapterTests(unittest.TestCase):
    @patch("kobayashi_benchmark.adapters._post_json")
    def test_cloud_api_key_is_sent_as_bearer_token(self, post_json):
        post_json.return_value = {
            "message": {"content": "response"},
            "done_reason": "stop",
        }
        adapter = OllamaAdapter(
            model="model-a",
            base_url="https://ollama.com",
            api_key="secret-token",
            provider="ollama-cloud",
        )

        result = adapter.generate("prompt", GenerationConfig())

        self.assertIsNone(result.error)
        self.assertEqual(post_json.call_args.args[2], {"Authorization": "Bearer secret-token"})


if __name__ == "__main__":
    unittest.main()
