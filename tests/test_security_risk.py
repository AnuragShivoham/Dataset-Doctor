import unittest

from ml_engine.core.result import Finding
from ml_engine.security.risk import assess_risk


class SecurityRiskTests(unittest.TestCase):
    def test_risk_levels_and_reason_summary(self):
        self.assertEqual(assess_risk([])["risk_level"], "low")
        medium = assess_risk([Finding("s", "potential_leakage", "high", "review")])
        self.assertEqual(medium["risk_level"], "medium")
        self.assertEqual(medium["high_severity_count"], 1)
        self.assertEqual(medium["reasons"], ["Potential leakage"])
        high = assess_risk([{"issue_type": "x", "severity": "low"}] * 6)
        self.assertEqual(high["risk_level"], "high")

    def test_thresholds_are_configurable_and_validated(self):
        findings = [{"issue_type": "x", "severity": "low"}] * 2
        self.assertEqual(assess_risk(findings, medium_finding_threshold=2)["risk_level"], "medium")
        with self.assertRaises(ValueError):
            assess_risk([], medium_finding_threshold=4, high_finding_threshold=3)


if __name__ == "__main__":
    unittest.main()
