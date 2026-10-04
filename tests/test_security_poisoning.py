import unittest

from ml_engine.core.result import Finding
from ml_engine.security.poisoning import aggregate_poisoning_indicators


class SecurityPoisoningTests(unittest.TestCase):
    def test_aggregates_independent_signals_for_a_record_cautiously(self):
        findings = [
            Finding("anomaly", "rare_category", "low", "rare", metadata={"records": ["r1"]}),
            Finding("leakage", "potential_leakage", "medium", "leak", metadata={"record": "r1"}),
            Finding("label", "possible_label_inconsistency", "high", "labels", metadata={"records": ["r1", "r2"]}),
        ]
        summary, results = aggregate_poisoning_indicators(findings)
        self.assertEqual(summary["potential_indicator_count"], 1)
        self.assertEqual(results[0].issue_type, "potential_poisoning_indicator")
        self.assertEqual(results[0].metadata["records"], ["r1"])
        self.assertIn("not a poisoning determination", results[0].message)

    def test_does_not_escalate_a_single_signal(self):
        _, results = aggregate_poisoning_indicators([
            Finding("anomaly", "rare_category", "low", "rare", metadata={"record": "r1"})
        ])
        self.assertEqual(results, [])

    def test_dataset_signals_need_distinct_issue_types(self):
        findings = [Finding("a", "unusual_missingness", "medium", "missing"),
                    Finding("b", "potential_leakage", "medium", "leak")]
        _, results = aggregate_poisoning_indicators(findings)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
