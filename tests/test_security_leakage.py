import unittest

from ml_engine.security.leakage import analyze_leakage


class SecurityLeakageTests(unittest.TestCase):
    def test_tabular_identifiers_target_names_and_copied_target(self):
        records = [{"row_id": str(index), "target": index % 2, "target_copy": index % 2,
                    "diagnosis_code": index % 2} for index in range(24)]
        summary, findings = analyze_leakage(records, target="target", modality="tabular")
        self.assertEqual(summary["status"], "indicators_found")
        self.assertTrue(all(item.issue_type == "potential_leakage" for item in findings))
        indicators = {item.metadata["indicator"] for item in findings}
        self.assertIn("identifier_like_column", indicators)
        self.assertIn("target_like_column", indicators)
        self.assertIn("target_value_copy", indicators)

    def test_text_mentions_labels_and_metadata_exposes_target(self):
        records = [{"id": "1", "text": "Diagnosis fracture confirmed", "label": "fracture", "target": "fracture"},
                   {"id": "2", "text": "fracture noted", "label": "fracture", "target": "fracture"},
                   {"id": "3", "text": "No finding", "label": "normal", "target": "normal"}]
        _, findings = analyze_leakage(records, target="target", modality="text")
        indicators = {item.metadata["indicator"] for item in findings}
        self.assertIn("label_mentioned_in_text", indicators)
        self.assertIn("target_in_metadata", indicators)

    def test_strong_numeric_target_association_is_reported_as_indicator(self):
        records = [{"feature": index * 2, "outcome": index} for index in range(10)]
        _, findings = analyze_leakage(records, target="outcome", modality="tabular")
        finding = next(item for item in findings if item.metadata["indicator"] == "strong_target_association")
        self.assertEqual(finding.issue_type, "potential_leakage")
        self.assertEqual(finding.metadata["metric"], "absolute_pearson_correlation")

    def test_image_filename_and_metadata_indicators(self):
        records = [{"id": "a", "filename": "fracture_01.png", "label": "fracture", "tag": "fracture"},
                   {"id": "b", "filename": "normal_02.png", "label": "normal", "tag": "normal"}]
        _, findings = analyze_leakage(records, target="label", modality="image")
        indicators = {item.metadata["indicator"] for item in findings}
        self.assertIn("label_in_filename", indicators)
        self.assertIn("label_in_metadata", indicators)

    def test_no_target_means_no_text_label_check_and_validation(self):
        _, findings = analyze_leakage([{"text": "label text"}], modality="text")
        self.assertEqual(findings, [])
        with self.assertRaises(ValueError):
            analyze_leakage([], modality="audio")
