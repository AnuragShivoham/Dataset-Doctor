import unittest

from ml_engine.text.statistics import analyze_statistics


class TextStatisticsTests(unittest.TestCase):
    def test_statistics_include_word_length_and_label_distribution(self):
        result = analyze_statistics([
            {"text": "one two", "label": "a"},
            {"text": "three four five", "label": "a"},
            {"text": "", "label": None},
        ], min_words=3, max_words=4)
        self.assertEqual(result["document_count"], 3)
        self.assertEqual(result["total_words"], 5)
        self.assertEqual(result["median_words"], 2.0)
        self.assertEqual(result["empty_documents"], 1)
        self.assertEqual(result["very_short_documents"], 1)
        self.assertEqual(result["label_distribution"], {"a": 2})
        self.assertEqual(result["unlabeled_documents"], 1)

    def test_statistics_empty_and_invalid_thresholds(self):
        self.assertEqual(analyze_statistics([])["average_words"], 0.0)
        with self.assertRaises(ValueError):
            analyze_statistics([], min_words=4, max_words=3)
