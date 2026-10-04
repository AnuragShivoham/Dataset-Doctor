import unittest

from ml_engine.text.pii import analyze_pii


class TextPiiTests(unittest.TestCase):
    def test_pii_reports_types_without_exposing_matched_values(self):
        summary, findings = analyze_pii([{"id": "doc-1", "text": "Contact alice@example.com at https://example.org"}])
        self.assertEqual(summary["pattern_counts"]["email"], 1)
        self.assertEqual(summary["pattern_counts"]["url"], 1)
        self.assertEqual(summary["documents_with_possible_pii"], 1)
        self.assertTrue(all("alice@example.com" not in str(finding.metadata) for finding in findings))
