import unittest

from ml_engine.security import analyze_anomalies


class SecurityAnomalyTests(unittest.TestCase):
    def test_numeric_extreme_has_evidence(self):
        records = [{"id": str(index), "measurement": value} for index, value in enumerate([10, 11, 9, 10, 12, 11, 1000])]
        summary, findings = analyze_anomalies(records)
        finding = next(item for item in findings if item.issue_type == "extreme_numeric_value")
        self.assertEqual(summary["numeric_anomaly_count"], 1)
        self.assertEqual(finding.metadata["records"][0]["id"], "6")
        self.assertEqual(finding.metadata["records"][0]["value"], 1000)

    def test_rare_low_cardinality_category_and_identifier_skip(self):
        records = ([{"id": f"{index}", "group": "common", "user_id": f"u{index}"} for index in range(99)]
                   + [{"id": "rare", "group": "unusual", "user_id": "u99"}])
        _, findings = analyze_anomalies(records)
        rare = [item for item in findings if item.issue_type == "rare_category"]
        self.assertEqual(len(rare), 1)
        self.assertEqual(rare[0].metadata["category"], "unusual")
        self.assertEqual(rare[0].column, "group")

    def test_unusual_missingness_includes_record_ids(self):
        records = [{"id": "a", "feature": None}, {"id": "b", "feature": " "},
                   {"id": "c", "feature": "present"}, {"id": "d", "feature": None}]
        _, findings = analyze_anomalies(records)
        finding = next(item for item in findings if item.issue_type == "unusual_missingness")
        self.assertEqual(finding.metadata["missing_count"], 3)
        self.assertEqual(finding.metadata["records"], ["a", "b", "d"])

    def test_empty_input_and_parameter_validation(self):
        summary, findings = analyze_anomalies([])
        self.assertEqual(summary["finding_count"], 0)
        self.assertEqual(findings, [])
        with self.assertRaises(ValueError):
            analyze_anomalies([], numeric_z_threshold=0)


if __name__ == "__main__":
    unittest.main()
