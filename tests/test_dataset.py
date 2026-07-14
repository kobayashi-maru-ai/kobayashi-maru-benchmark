import unittest

from kobayashi_benchmark.dataset import build_samples, dataset_digest, pilot_samples


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = build_samples()

    def test_expected_release_shape(self):
        self.assertEqual(len(self.samples), 180)
        counts = {}
        for sample in self.samples:
            counts[sample.suite] = counts.get(sample.suite, 0) + 1
        self.assertEqual(
            counts,
            {
                "military_identity": 60,
                "military_neutral": 30,
                "police_identity": 60,
                "police_neutral": 30,
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
            if sample.identity_direction == "neutral":
                continue
            key = (sample.counterfactual_group, sample.language, sample.paraphrase)
            pairs.setdefault(key, set()).add(sample.identity_direction)
        self.assertTrue(pairs)
        self.assertTrue(all(directions == {"a_to_b", "b_to_a"} for directions in pairs.values()))

    def test_languages_are_separate_and_balanced(self):
        counts = {"es": 0, "en": 0}
        for sample in self.samples:
            counts[sample.language] += 1
        self.assertEqual(counts, {"es": 90, "en": 90})

    def test_pilot_is_balanced_across_suites_and_languages(self):
        pilot = pilot_samples(self.samples)
        self.assertEqual(len(pilot), 12)
        self.assertEqual({sample.suite for sample in pilot}, {
            "military_neutral",
            "military_identity",
            "police_neutral",
            "police_identity",
        })
        self.assertEqual({sample.language for sample in pilot}, {"es", "en"})
        directions = {sample.identity_direction for sample in pilot}
        self.assertEqual(directions, {"neutral", "a_to_b", "b_to_a"})


if __name__ == "__main__":
    unittest.main()
