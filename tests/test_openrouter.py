import copy
import importlib
import importlib.util
import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import quote

from kobayashi_benchmark.adapters import BudgetExceeded, CostBudget, OpenRouterModelSpec
from kobayashi_benchmark.models import GenerationConfig

MODULE_NAME = "kobayashi_benchmark.openrouter"


def _openrouter():
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, (
        "kobayashi_benchmark.openrouter must implement the cohort preflight contract"
    )
    return importlib.import_module(MODULE_NAME)


class OpenRouterCohortTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.directory = Path(temporary_directory.name)

    def make_manifest(self, count=15):
        return {
            "schema_version": 1,
            "model_count": count,
            "models": [
                {
                    "model_id": f"lab/model-{index}",
                    "canonical_slug": f"lab/model-{index}-20260715",
                    "endpoint_tag": f"provider-{index}",
                    "provider_name": f"Provider {index}",
                    "quantization": "bf16",
                    "request_parameters": [
                        "temperature",
                        "top_p",
                        "max_tokens",
                        "seed",
                        *(["reasoning"] if index == 0 else []),
                    ],
                    "reasoning": {"enabled": False} if index == 0 else None,
                    "price_snapshot": {
                        "prompt": "0.0000001",
                        "completion": "0.0000002",
                    },
                }
                for index in range(count)
            ],
        }

    def write_manifest(self, manifest):
        path = self.directory / "cohort.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def make_live_payloads(self, manifest, *, prompt="0.001", completion="0.002"):
        models = []
        endpoints = {}
        for entry in manifest["models"]:
            supported_parameters = list(entry["request_parameters"])
            models.append(
                {
                    "id": entry["model_id"],
                    "canonical_slug": entry["canonical_slug"],
                }
            )
            endpoints[entry["model_id"]] = {
                "data": {
                    "id": entry["model_id"],
                    "endpoints": [
                        {
                            "tag": entry["endpoint_tag"],
                            "name": (f"{entry['provider_name']} | {entry['canonical_slug']}"),
                            "provider_name": entry["provider_name"],
                            "model_id": entry["model_id"],
                            "quantization": entry["quantization"],
                            "status": 0,
                            "supported_parameters": supported_parameters,
                            "pricing": {
                                "prompt": prompt,
                                "completion": completion,
                            },
                        }
                    ],
                }
            }
        return {"data": models}, endpoints

    def make_get_json(self, catalogue, endpoints):
        calls = []

        def get_json(url):
            calls.append(url)
            if url == "https://openrouter.ai/api/v1/models":
                return catalogue
            for model_id, payload in endpoints.items():
                encoded_id = quote(model_id, safe="/")
                if url == f"https://openrouter.ai/api/v1/models/{encoded_id}/endpoints":
                    return payload
            raise AssertionError(f"unexpected public GET URL: {url}")

        return get_json, calls

    def assert_bounded_error(self, error):
        self.assertLessEqual(len(str(error)), 240)

    def preflight(self, manifest, catalogue, endpoints, **overrides):
        openrouter = _openrouter()
        get_json, calls = self.make_get_json(catalogue, endpoints)
        values = {
            "manifest_path": self.write_manifest(manifest),
            "samples": [SimpleNamespace(prompt="A"), SimpleNamespace(prompt="é")],
            "config": GenerationConfig(max_tokens=3),
            "budget": CostBudget(Decimal("5")),
            "get_json": get_json,
            "system_prompt": "§",
        }
        values.update(overrides)
        return openrouter.preflight_openrouter_cohort(**values), calls

    def test_loads_a_valid_v1_manifest_into_exactly_fifteen_specs(self):
        openrouter = _openrouter()
        manifest = self.make_manifest()

        specs = openrouter.load_cohort_manifest(self.write_manifest(manifest))

        self.assertIsInstance(specs, tuple)
        self.assertEqual(len(specs), 15)
        self.assertEqual(specs[0].model_id, "lab/model-0")
        self.assertEqual(specs[0].provider_name, "Provider 0")
        self.assertEqual(
            specs[0].supported_parameters, frozenset(manifest["models"][0]["request_parameters"])
        )
        self.assertEqual(specs[0].reasoning, {"enabled": False})
        self.assertEqual(specs[0].prompt_price, Decimal("0.0000001"))
        self.assertEqual(specs[0].completion_price, Decimal("0.0000002"))

    def test_manifest_count_cannot_override_the_fixed_fifteen_model_cohort(self):
        openrouter = _openrouter()
        one_model_manifest = self.make_manifest(count=1)

        with self.assertRaises(openrouter.OpenRouterManifestError):
            openrouter.load_cohort_manifest(
                self.write_manifest(one_model_manifest), expected_count=1
            )

    def test_manifest_rejects_wrong_shape_missing_fields_and_invalid_reasoning(self):
        openrouter = _openrouter()
        mutations = {
            "schema version": lambda value: value.update(schema_version=2),
            "declared count": lambda value: value.update(model_count=14),
            "actual count": lambda value: value["models"].pop(),
            "missing snapshot": lambda value: value["models"][0].pop("price_snapshot"),
            "blank quantization": lambda value: value["models"][0].update(quantization=" "),
            "blank provider": lambda value: value["models"][0].update(provider_name=""),
            "empty parameters": lambda value: value["models"][0].update(request_parameters=[]),
            "invalid reasoning": lambda value: value["models"][0].update(reasoning=[]),
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                manifest = self.make_manifest()
                mutate(manifest)
                with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
                    openrouter.load_cohort_manifest(self.write_manifest(manifest))
                self.assert_bounded_error(caught.exception)

    def test_manifest_requires_every_entry_and_price_snapshot_field(self):
        openrouter = _openrouter()
        entry_fields = (
            "model_id",
            "canonical_slug",
            "endpoint_tag",
            "provider_name",
            "quantization",
            "request_parameters",
            "reasoning",
            "price_snapshot",
        )

        for field in entry_fields:
            with self.subTest(missing_entry_field=field):
                manifest = self.make_manifest()
                manifest["models"][0].pop(field)
                with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
                    openrouter.load_cohort_manifest(self.write_manifest(manifest))
                self.assert_bounded_error(caught.exception)

        for field in ("prompt", "completion"):
            with self.subTest(missing_snapshot_field=field):
                manifest = self.make_manifest()
                manifest["models"][0]["price_snapshot"].pop(field)
                with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
                    openrouter.load_cohort_manifest(self.write_manifest(manifest))
                self.assert_bounded_error(caught.exception)

    def test_manifest_rejects_invalid_snapshot_types_and_prices(self):
        openrouter = _openrouter()
        invalid_values = (None, [], "0", "-0.1", "NaN", "Infinity")

        manifest = self.make_manifest()
        manifest["models"][0]["price_snapshot"] = []
        with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
            openrouter.load_cohort_manifest(self.write_manifest(manifest))
        self.assert_bounded_error(caught.exception)

        for field in ("prompt", "completion"):
            for invalid in invalid_values:
                with self.subTest(field=field, invalid=invalid):
                    manifest = self.make_manifest()
                    manifest["models"][0]["price_snapshot"][field] = invalid
                    with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
                        openrouter.load_cohort_manifest(self.write_manifest(manifest))
                    self.assert_bounded_error(caught.exception)

    def test_manifest_requires_reasoning_in_parameters_when_configured(self):
        openrouter = _openrouter()
        manifest = self.make_manifest()
        manifest["models"][0]["request_parameters"].remove("reasoning")

        with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
            openrouter.load_cohort_manifest(self.write_manifest(manifest))

        self.assert_bounded_error(caught.exception)

    def test_manifest_requires_exactly_one_output_cap_parameter(self):
        openrouter = _openrouter()
        for mode in ("missing", "both"):
            with self.subTest(mode=mode):
                manifest = self.make_manifest()
                parameters = manifest["models"][0]["request_parameters"]
                if mode == "missing":
                    parameters.remove("max_tokens")
                else:
                    parameters.append("max_completion_tokens")

                with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
                    openrouter.load_cohort_manifest(self.write_manifest(manifest))

                self.assert_bounded_error(caught.exception)

    def test_manifest_rejects_duplicate_or_blank_pinned_identities(self):
        openrouter = _openrouter()
        fields = ("model_id", "canonical_slug", "endpoint_tag")

        for field in fields:
            for mode in ("duplicate", "blank"):
                with self.subTest(field=field, mode=mode):
                    manifest = self.make_manifest()
                    manifest["models"][1][field] = (
                        manifest["models"][0][field] if mode == "duplicate" else " "
                    )
                    with self.assertRaises(openrouter.OpenRouterManifestError) as caught:
                        openrouter.load_cohort_manifest(self.write_manifest(manifest))
                    self.assert_bounded_error(caught.exception)

    def test_resolves_all_models_with_live_prices_and_conservative_projection(self):
        manifest = self.make_manifest()
        catalogue, endpoints = self.make_live_payloads(manifest)

        with (
            patch.dict(os.environ, {"OPENROUTER_API_KEY": "credential-sentinel"}),
            patch("os.getenv") as getenv,
            patch("kobayashi_benchmark.adapters._post_json") as post_json,
        ):
            result, get_calls = self.preflight(manifest, catalogue, endpoints)

        self.assertIsInstance(result.specs, tuple)
        self.assertTrue(all(isinstance(spec, OpenRouterModelSpec) for spec in result.specs))
        self.assertEqual(result.model_count, 15)
        self.assertEqual(result.calls, 30)
        self.assertEqual(result.projected_usd, Decimal("0.285"))
        self.assertTrue(all(spec.prompt_price == Decimal("0.001") for spec in result.specs))
        self.assertTrue(all(spec.completion_price == Decimal("0.002") for spec in result.specs))
        self.assertEqual(get_calls[0], "https://openrouter.ai/api/v1/models")
        self.assertEqual(len(get_calls), 16)
        self.assertIn(
            "https://openrouter.ai/api/v1/models/lab/model-0/endpoints",
            get_calls,
        )
        self.assertNotIn("credential-sentinel", repr(result))
        getenv.assert_not_called()
        post_json.assert_not_called()

    def test_rejects_catalogue_canonical_drift(self):
        openrouter = _openrouter()
        manifest = self.make_manifest()
        catalogue, endpoints = self.make_live_payloads(manifest)
        catalogue["data"][0]["canonical_slug"] = "lab/drifted"

        with self.assertRaises(openrouter.OpenRouterPreflightError) as caught:
            self.preflight(manifest, catalogue, endpoints)

        self.assert_bounded_error(caught.exception)

    def test_rejects_endpoint_identity_provider_quantization_and_health_drift(self):
        openrouter = _openrouter()
        mutations = {
            "model id": lambda endpoint: endpoint.update(model_id="lab/drifted"),
            "canonical": lambda endpoint: endpoint.update(name="Provider 0 | lab/drifted"),
            "provider": lambda endpoint: endpoint.update(provider_name="Wrong Provider"),
            "quantization": lambda endpoint: endpoint.update(quantization="int4"),
            "route": lambda endpoint: endpoint.update(tag="wrong-route"),
            "health": lambda endpoint: endpoint.update(status=-1),
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                manifest = self.make_manifest()
                catalogue, endpoints = self.make_live_payloads(manifest)
                mutate(endpoints["lab/model-0"]["data"]["endpoints"][0])
                with self.assertRaises(openrouter.OpenRouterPreflightError) as caught:
                    self.preflight(manifest, catalogue, endpoints)
                self.assert_bounded_error(caught.exception)

    def test_rejects_more_than_one_healthy_endpoint_for_the_pinned_tag(self):
        openrouter = _openrouter()
        manifest = self.make_manifest()
        catalogue, endpoints = self.make_live_payloads(manifest)
        duplicate = copy.deepcopy(endpoints["lab/model-0"]["data"]["endpoints"][0])
        endpoints["lab/model-0"]["data"]["endpoints"].append(duplicate)

        with self.assertRaises(openrouter.OpenRouterPreflightError) as caught:
            self.preflight(manifest, catalogue, endpoints)

        self.assert_bounded_error(caught.exception)

    def test_rejects_missing_live_request_or_reasoning_parameters(self):
        openrouter = _openrouter()
        for missing in ("seed", "reasoning"):
            with self.subTest(missing=missing):
                manifest = self.make_manifest()
                catalogue, endpoints = self.make_live_payloads(manifest)
                supported = endpoints["lab/model-0"]["data"]["endpoints"][0]["supported_parameters"]
                supported.remove(missing)
                with self.assertRaises(openrouter.OpenRouterPreflightError) as caught:
                    self.preflight(manifest, catalogue, endpoints)
                self.assert_bounded_error(caught.exception)

    def test_rejects_non_finite_non_positive_or_missing_live_prices(self):
        openrouter = _openrouter()
        for field in ("prompt", "completion"):
            for invalid in (None, "0", "-0.1", "NaN", "Infinity"):
                with self.subTest(field=field, invalid=invalid):
                    manifest = self.make_manifest()
                    catalogue, endpoints = self.make_live_payloads(manifest)
                    pricing = endpoints["lab/model-0"]["data"]["endpoints"][0]["pricing"]
                    if invalid is None:
                        pricing.pop(field)
                    else:
                        pricing[field] = invalid
                    with self.assertRaises(openrouter.OpenRouterPreflightError) as caught:
                        self.preflight(manifest, catalogue, endpoints)
                    self.assert_bounded_error(caught.exception)

    def test_budget_refuses_a_projection_equal_to_or_above_five_dollars(self):
        openrouter = _openrouter()
        for label, last_completion_price in (("equal", "0.18"), ("above", "0.1801")):
            with self.subTest(label=label):
                manifest = self.make_manifest()
                catalogue, endpoints = self.make_live_payloads(
                    manifest, prompt="0.1", completion="0.13"
                )
                endpoint = endpoints["lab/model-14"]["data"]["endpoints"][0]
                endpoint["pricing"]["completion"] = last_completion_price
                get_json, _ = self.make_get_json(catalogue, endpoints)

                with self.assertRaises(BudgetExceeded):
                    openrouter.preflight_openrouter_cohort(
                        manifest_path=self.write_manifest(manifest),
                        samples=[SimpleNamespace(prompt="aa")],
                        config=GenerationConfig(max_tokens=1),
                        budget=CostBudget(Decimal("5")),
                        get_json=get_json,
                    )


if __name__ == "__main__":
    unittest.main()
