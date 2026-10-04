import unittest

from ml_engine.text.quality import analyze_quality


class TextQualityTests(unittest.TestCase):
    def test_quality_flags_empty_short_and_long_records(self):
        summary, findings = analyze_quality([
            {"id": "empty", "text": " "},
            {"id": "short", "text": "one two"},
            {"id": "long", "text": "one two three four"},
        ], min_words=3, max_words=3)
        self.assertEqual(summary["empty_documents"], 1)
        self.assertEqual(summary["very_short_documents"], 1)
        self.assertEqual(summary["very_long_documents"], 1)
        self.assertEqual({finding.metadata["document"] for finding in findings}, {"empty", "short", "long"})
