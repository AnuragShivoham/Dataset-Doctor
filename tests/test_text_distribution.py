import unittest

from ml_engine.text.distribution import analyze_distribution


class TextDistributionTests(unittest.TestCase):
    def test_distribution_counts_labels_and_flags_imbalance(self):
        summary, findings = analyze_distribution([
            {"label": "major"}, {"label": "major"}, {"label": "major"}, {"label": "minor"}, {"label": None}
        ], imbalance_threshold=3)
        self.assertEqual(summary["classes"]["major"]["count"], 3)
        self.assertEqual(summary["minority_class"], "minor")
        self.assertEqual(summary["unlabeled_documents"], 1)
        self.assertEqual(len(findings), 1)
