import io
import json
import unittest
import urllib.error
from decimal import Decimal
from unittest.mock import patch

from kobayashi_benchmark import adapters
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


class CostBudgetTests(unittest.TestCase):
    def make_budget(self, limit: str = "5"):
        self.assertTrue(
            hasattr(adapters, "CostBudget"),
            "kobayashi_benchmark.adapters must expose CostBudget",
        )
        return adapters.CostBudget(limit=Decimal(limit))

    def budget_exceeded(self):
        self.assertTrue(
            hasattr(adapters, "BudgetExceeded"),
            "kobayashi_benchmark.adapters must expose BudgetExceeded",
        )
        return adapters.BudgetExceeded

    def test_preflight_accepts_only_a_projection_strictly_below_the_limit(self):
        budget = self.make_budget()

        budget.preflight(Decimal("4.999999"))
        with self.assertRaises(self.budget_exceeded()):
            budget.preflight(Decimal("5"))
        with self.assertRaises(self.budget_exceeded()):
            budget.preflight(Decimal("5.000001"))

        self.assertEqual(budget.spent, Decimal("0"))

    def test_preflight_does_not_add_spend_to_the_complete_projected_total(self):
        budget = self.make_budget()
        budget.charge(Decimal("2"))

        budget.preflight(Decimal("4"))
        with self.assertRaises(self.budget_exceeded()):
            budget.preflight(Decimal("5"))

        self.assertEqual(budget.spent, Decimal("2"))

    def test_authorize_accounts_for_spend_and_refuses_the_exact_limit(self):
        budget = self.make_budget()
        budget.charge(Decimal("1.25"))

        budget.authorize(Decimal("3.749999"))
        with self.assertRaises(self.budget_exceeded()):
            budget.authorize(Decimal("3.75"))
        with self.assertRaises(self.budget_exceeded()):
            budget.authorize(Decimal("4"))

        self.assertEqual(budget.spent, Decimal("1.25"))

    def test_charge_uses_exact_decimal_arithmetic_and_returns_cumulative_spend(self):
        budget = self.make_budget()

        self.assertEqual(budget.charge(Decimal("0.10")), Decimal("0.10"))
        self.assertEqual(budget.charge(Decimal("0.20")), Decimal("0.30"))
        self.assertEqual(budget.spent, Decimal("0.30"))

    def test_charge_never_moves_spend_to_or_above_the_limit(self):
        budget = self.make_budget()
        budget.charge(Decimal("4.99"))

        with self.assertRaises(self.budget_exceeded()):
            budget.charge(Decimal("0.01"))
        with self.assertRaises(self.budget_exceeded()):
            budget.charge(Decimal("0.02"))

        self.assertEqual(budget.spent, Decimal("4.99"))

    def test_budget_operations_reject_negative_and_non_finite_amounts(self):
        budget = self.make_budget()
        invalid_amounts = (
            Decimal("-0.01"),
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
        )

        for operation in (budget.preflight, budget.authorize, budget.charge):
            for amount in invalid_amounts:
                with self.subTest(operation=operation.__name__, amount=amount):
                    with self.assertRaises(ValueError):
                        operation(amount)

        self.assertEqual(budget.spent, Decimal("0"))


class OpenRouterAdapterTests(unittest.TestCase):
    def make_spec(self, **overrides):
        self.assertTrue(
            hasattr(adapters, "OpenRouterModelSpec"),
            "kobayashi_benchmark.adapters must expose OpenRouterModelSpec",
        )
        values = {
            "model_id": "lab/model-a",
            "canonical_slug": "lab/model-a-20260715",
            "endpoint_tag": "provider-a",
            "quantization": "bf16",
            "supported_parameters": frozenset(
                {"temperature", "top_p", "max_tokens", "seed", "reasoning"}
            ),
            "reasoning": {"enabled": False},
            "prompt_price": Decimal("0.0001"),
            "completion_price": Decimal("0.0002"),
        }
        values.update(overrides)
        return adapters.OpenRouterModelSpec(**values)

    def make_adapter(self, *, budget=None, spec=None, api_key="test-token"):
        self.assertTrue(
            hasattr(adapters, "OpenRouterAdapter"),
            "kobayashi_benchmark.adapters must expose OpenRouterAdapter",
        )
        return adapters.OpenRouterAdapter(
            spec=spec or self.make_spec(),
            api_key=api_key,
            budget=budget or adapters.CostBudget(Decimal("5")),
        )

    def successful_response(self, *, returned_model="lab/model-a-20260715", cost="0.03"):
        return {
            "id": "generation-1",
            "model": returned_model,
            "system_fingerprint": "fingerprint-a",
            "service_tier": "default",
            "openrouter_metadata": {
                "requested": "lab/model-a-20260715",
                "strategy": "direct",
                "attempt": 1,
                "endpoints": {
                    "total": 1,
                    "available": [
                        {
                            "provider": "Provider A",
                            "model": "lab/model-a-20260715",
                            "selected": True,
                        }
                    ],
                },
            },
            "choices": [
                {
                    "message": {"content": "response", "reasoning": "private trace"},
                    "finish_reason": "stop",
                    "native_finish_reason": "STOP",
                }
            ],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 7,
                "cost": cost,
                "prompt_tokens_details": {"cached_tokens": 4},
                "completion_tokens_details": {"reasoning_tokens": 2},
            },
        }

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_request_pins_route_headers_and_only_supported_parameters(self, post_json):
        post_json.return_value = self.successful_response()
        spec = self.make_spec(
            supported_parameters=frozenset({"temperature", "max_tokens", "reasoning"}),
            reasoning={"effort": "low"},
        )
        budget = adapters.CostBudget(Decimal("5"))
        adapter = self.make_adapter(spec=spec, budget=budget)

        result = adapter.generate(
            "prompt",
            GenerationConfig(
                temperature=0.25,
                top_p=0.75,
                max_tokens=20,
                seed=7,
                thinking="high",
            ),
            system_prompt="system",
        )

        self.assertIsNone(result.error)
        self.assertEqual(adapter.model, spec.model_id)
        self.assertEqual(adapter.provider, "openrouter")
        url, payload, headers, _timeout = post_json.call_args.args
        self.assertEqual(url, "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(payload["model"], spec.canonical_slug)
        self.assertEqual(
            payload["provider"],
            {
                "only": [spec.endpoint_tag],
                "allow_fallbacks": False,
                "require_parameters": True,
                "data_collection": "deny",
            },
        )
        self.assertEqual(
            payload["messages"],
            [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "prompt"},
            ],
        )
        self.assertEqual(payload["temperature"], 0.25)
        self.assertEqual(payload["max_tokens"], 20)
        self.assertEqual(payload["reasoning"], {"effort": "low"})
        self.assertNotIn("top_p", payload)
        self.assertNotIn("seed", payload)
        self.assertNotIn("thinking", payload)
        self.assertFalse(payload["stream"])
        self.assertEqual(headers["Authorization"], "Bearer test-token")
        self.assertEqual(headers["X-OpenRouter-Metadata"], "enabled")

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_budget_authorization_uses_utf8_bytes_and_happens_before_post(self, post_json):
        spec = self.make_spec(
            supported_parameters=frozenset(),
            reasoning=None,
            prompt_price=Decimal("0.1"),
            completion_price=Decimal("0.2"),
        )
        budget = adapters.CostBudget(Decimal("0.7"))
        adapter = self.make_adapter(spec=spec, budget=budget)

        result = adapter.generate("é", GenerationConfig(max_tokens=2), system_prompt="A")

        self.assertIn("budget", result.error.lower())
        post_json.assert_not_called()
        self.assertEqual(budget.spent, Decimal("0"))

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_usage_route_and_finish_metadata_are_normalized_and_json_serializable(
        self, post_json
    ):
        post_json.return_value = self.successful_response(
            returned_model="lab/model-a", cost="0.001230"
        )
        budget = adapters.CostBudget(Decimal("5"))
        spec = self.make_spec(reasoning={"enabled": False})
        adapter = self.make_adapter(spec=spec, budget=budget)

        result = adapter.generate("prompt", GenerationConfig())

        self.assertIsNone(result.error)
        self.assertEqual(result.text, "response")
        self.assertEqual(result.prompt_tokens, 12)
        self.assertEqual(result.completion_tokens, 7)
        self.assertEqual(budget.spent, Decimal("0.001230"))
        self.assertEqual(
            result.provider_metadata,
            {
                "generation_id": "generation-1",
                "returned_model": "lab/model-a",
                "canonical_model": spec.canonical_slug,
                "endpoint_tag": "provider-a",
                "quantization": "bf16",
                "done_reason": "stop",
                "native_finish_reason": "STOP",
                "system_fingerprint": "fingerprint-a",
                "service_tier": "default",
                "thinking_mode": {"enabled": False},
                "reasoning_tokens": 2,
                "prompt_tokens": 12,
                "completion_tokens": 7,
                "cached_tokens": 4,
                "billed_usd": "0.001230",
                "openrouter_metadata": self.successful_response()[
                    "openrouter_metadata"
                ],
                "request_parameters": [
                    "max_tokens",
                    "reasoning",
                    "seed",
                    "temperature",
                    "top_p",
                ],
            },
        )
        json.dumps(result.to_dict())

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_billed_cost_is_charged_before_returned_identity_is_rejected(self, post_json):
        post_json.return_value = self.successful_response(
            returned_model="different/model", cost="0.12"
        )
        budget = adapters.CostBudget(Decimal("5"))
        adapter = self.make_adapter(budget=budget)

        result = adapter.generate("prompt", GenerationConfig())

        self.assertIn("identity mismatch", result.error.lower())
        self.assertEqual(result.text, "")
        self.assertEqual(budget.spent, Decimal("0.12"))

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_billed_cost_is_charged_before_empty_content_is_rejected(self, post_json):
        response = self.successful_response(cost="0.08")
        response["choices"][0]["message"]["content"] = "   "
        post_json.return_value = response
        budget = adapters.CostBudget(Decimal("5"))
        adapter = self.make_adapter(budget=budget)

        result = adapter.generate("prompt", GenerationConfig())

        self.assertIn("empty final response", result.error.lower())
        self.assertEqual(result.text, "")
        self.assertEqual(budget.spent, Decimal("0.08"))

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_missing_or_malformed_cost_fails_without_mutating_spend(self, post_json):
        responses = []
        missing = self.successful_response()
        del missing["usage"]["cost"]
        responses.append(missing)
        for invalid_cost in ("not-a-cost", "NaN", "Infinity", "-0.01"):
            responses.append(self.successful_response(cost=invalid_cost))

        for response in responses:
            with self.subTest(cost=response["usage"].get("cost")):
                post_json.return_value = response
                budget = adapters.CostBudget(Decimal("5"))
                adapter = self.make_adapter(budget=budget)

                result = adapter.generate("prompt", GenerationConfig())

                self.assertIn("cost", result.error.lower())
                self.assertEqual(result.text, "")
                self.assertEqual(budget.spent, Decimal("0"))

    @patch("kobayashi_benchmark.adapters._post_json")
    def test_http_and_provider_errors_are_bounded_and_redacted_without_retry(self, post_json):
        api_key = "test-token"
        adapter = self.make_adapter(api_key=api_key)
        http_error = urllib.error.HTTPError(
            "https://openrouter.ai/api/v1/chat/completions",
            401,
            "reason-containing-test-token",
            {"X-Leak": "header-secret"},
            io.BytesIO(b"response-body-secret"),
        )
        cases = (
            (http_error, "http"),
            (
                {
                    "error": {
                        "code": 429,
                        "message": "provider-secret response-body-secret test-token",
                    }
                },
                "provider",
            ),
        )

        for response_or_error, error_kind in cases:
            with self.subTest(error_kind=error_kind):
                post_json.reset_mock()
                if isinstance(response_or_error, Exception):
                    post_json.side_effect = response_or_error
                    post_json.return_value = None
                else:
                    post_json.side_effect = None
                    post_json.return_value = response_or_error

                result = adapter.generate("prompt", GenerationConfig())

                self.assertIn(error_kind, result.error.lower())
                self.assertLessEqual(len(result.error), 120)
                for forbidden in (
                    api_key,
                    "response-body-secret",
                    "header-secret",
                    "provider-secret",
                ):
                    self.assertNotIn(forbidden, result.error)
                post_json.assert_called_once()

if __name__ == "__main__":
    unittest.main()
