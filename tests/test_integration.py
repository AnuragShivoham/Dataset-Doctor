import unittest

from ml_engine import analyze_tabular


class IntegrationTests(unittest.TestCase):
    def test_public_result_contract_and_balanced_target(self):
        result = analyze_tabular("sample-data/test.csv", target_column="Target")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["dataset"], {"rows": 6, "columns": 4})
        self.assertIn("health", result)
        self.assertIn("findings", result)
        self.assertIn("recommendations", result)
        balance = result["summary"]["imbalance"]
        self.assertEqual(balance["imbalance_ratio"], 1.0)
        self.assertEqual(balance["status"], "healthy")
        self.assertIsNone(balance["minority_class"])
        self.assertIsNone(balance["majority_class"])
        self.assertNotIn("class_imbalance", [finding["issue_type"] for finding in result["findings"]])
        self.assertEqual(result["health"]["components"]["balance"], 100.0)
