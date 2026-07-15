import unittest

from kobayashi_benchmark.dataset import build_samples, dataset_digest, pilot_samples


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = build_samples()

    def test_expected_release_shape(self):
        self.assertEqual(len(self.samples), 20)
        counts = {}
        for sample in self.samples:
            counts[sample.suite] = counts.get(sample.suite, 0) + 1
        self.assertEqual(
            counts,
            {
                "armed_conflict": 6,
                "civil_security": 6,
                "critical_infrastructure": 4,
                "humanitarian_crisis": 4,
            },
        )

    def test_ids_are_unique_and_digest_is_stable(self):
        self.assertEqual(len({sample.id for sample in self.samples}), len(self.samples))
        digest = dataset_digest(self.samples)
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, dataset_digest(build_samples()))

    def test_every_identity_case_has_a_mirrored_pair(self):
        pairs = {}
        for sample in self.samples:
            key = (sample.counterfactual_group, sample.language, sample.paraphrase)
            pairs.setdefault(key, set()).add(sample.identity_direction)
        self.assertTrue(pairs)
        self.assertTrue(all(directions == {"a_to_b", "b_to_a"} for directions in pairs.values()))

    def test_release_is_english_only(self):
        self.assertEqual({sample.language for sample in self.samples}, {"en"})

    def test_core_profile_contains_all_twenty_prompts(self):
        pilot = pilot_samples(self.samples)
        self.assertEqual(len(pilot), 20)
        self.assertEqual({sample.suite for sample in pilot}, {
            "armed_conflict",
            "civil_security",
            "critical_infrastructure",
            "humanitarian_crisis",
        })
        self.assertEqual({sample.language for sample in pilot}, {"en"})
        directions = {sample.identity_direction for sample in pilot}
        self.assertEqual(directions, {"a_to_b", "b_to_a"})

    def test_prompts_use_real_symmetric_identities_without_reassurance_preamble(self):
        banned = {
            "Consider a theoretical and hypothetical exercise",
            "You are an AI designed to act responsibly",
            "Borean",
            "Asterian",
        }
        for sample in self.samples:
            self.assertIn("Israeli", sample.prompt)
            self.assertIn("Palestinian", sample.prompt)
            self.assertTrue(all(term not in sample.prompt for term in banned))

        for group in {sample.counterfactual_group for sample in self.samples}:
            pair = [sample for sample in self.samples if sample.counterfactual_group == group]
            self.assertEqual(len(pair), 2)
            normalized = {
                sample.prompt.replace("Israeli", "IDENTITY").replace("Palestinian", "IDENTITY")
                for sample in pair
            }
            self.assertEqual(len(normalized), 1)


if __name__ == "__main__":
    unittest.main()
