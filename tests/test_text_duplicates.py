import unittest

from ml_engine.text.duplicates import analyze_duplicates, normalize_text


class TextDuplicateTests(unittest.TestCase):
    def test_exact_and_normalized_duplicates(self):
        self.assertEqual(normalize_text(" Hello  WORLD "), "hello world")
        summary, findings = analyze_duplicates([
            {"id": "a", "text": "same"},
            {"id": "b", "text": "same"},
            {"id": "c", "text": " SAME  "},
        ])
        self.assertEqual(summary["exact_duplicate_groups"], 1)
        self.assertEqual(summary["normalized_duplicate_groups"], 1)
        self.assertEqual(summary["duplicate_documents"], 2)
        self.assertEqual(len(findings), 2)
