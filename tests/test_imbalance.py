import unittest

import pandas as pd

from ml_engine.tabular.imbalance import analyze_imbalance


class ImbalanceTests(unittest.TestCase):
    def test_balanced_target_has_no_finding_or_majority(self):
        summary, findings, _ = analyze_imbalance(pd.DataFrame({"y": [0, 0, 0, 1, 1, 1]}), "y")
        self.assertEqual(summary["imbalance_ratio"], 1.0)
        self.assertEqual(summary["status"], "healthy")
        self.assertIsNone(summary["minority_class"])
        self.assertIsNone(summary["majority_class"])
        self.assertFalse(findings)

    def test_imbalanced_target(self):
        summary, findings, _ = analyze_imbalance(pd.DataFrame({"y": [0] * 9 + [1]}), "y")
        self.assertEqual(summary["imbalance_ratio"], 9.0)
        self.assertEqual(summary["minority_class"], 1)
        self.assertTrue(findings)
