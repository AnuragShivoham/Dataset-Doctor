import unittest

import pandas as pd

from ml_engine.tabular.leakage import analyze_leakage


class LeakageTests(unittest.TestCase):
    def test_identifier_name_flagged(self):
        _, findings, _ = analyze_leakage(pd.DataFrame({"Customer_ID": [1, 2, 3]}))
        self.assertEqual(findings[0].issue_type, "possible_data_leakage")

    def test_no_target_relationship_check_without_target(self):
        summary, findings, _ = analyze_leakage(pd.DataFrame({"feature": [0, 1, 0, 1], "target": [0, 1, 0, 1]}))
        self.assertIsNone(summary["target_column"])
        self.assertFalse(summary["suspicious_target_relationships"])
        self.assertFalse(findings)
