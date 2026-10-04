import tempfile
import unittest
from pathlib import Path

from ml_engine.security.label_consistency import analyze_label_consistency


class SecurityLabelConsistencyTests(unittest.TestCase):
    def test_normalized_and_near_identical_text_with_conflicting_labels(self):
        records = [{"id": "a", "text": "Patient has bone fracture confirmed today.", "label": "fracture"},
                   {"id": "b", "text": "patient has bone fracture confirmed today!", "label": "normal"},
                   {"id": "c", "text": "A completely unrelated example sentence.", "label": "normal"}]
        summary, findings = analyze_label_consistency(records, similarity_threshold=0.9)
        self.assertEqual(summary["inconsistent_pairs"], 1)
        self.assertEqual(findings[0].issue_type, "possible_label_inconsistency")
        self.assertEqual(findings[0].metadata["records"], ["a", "b"])
        self.assertEqual(findings[0].metadata["labels"], ["fracture", "normal"])

    def test_byte_identical_files_with_conflicting_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder) / "one.bin", Path(folder) / "two.bin"
            first.write_bytes(b"same sample")
            second.write_bytes(b"same sample")
            records = [{"id": "one", "path": first, "label": "a"},
                       {"id": "two", "path": second, "label": "b"}]
            _, findings = analyze_label_consistency(records)
            self.assertEqual(findings[0].metadata["method"], "sha256")

    def test_skips_unlabeled_and_enforces_pairwise_limit(self):
        _, findings = analyze_label_consistency([{"text": "same", "label": None}, {"text": "same", "label": "a"}])
        self.assertEqual(findings, [])
        with self.assertRaises(ValueError):
            analyze_label_consistency([{}, {}, {}], max_records=2)
