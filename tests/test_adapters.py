import unittest
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


if __name__ == "__main__":
    unittest.main()
