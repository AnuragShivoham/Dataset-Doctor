import unittest

from ml_engine import analyze_text_dataset
from ml_engine.text.analyzer import TextHealthScoreConfig


class TextAnalyzerTests(unittest.TestCase):
    def test_analyzer_returns_standard_contract_and_finds_quality_issues(self):
        records = [
            {"id": "1", "text": "", "label": "major"},
            {"id": "2", "text": "one two", "label": "major"},
            {"id": "3", "text": "one two", "label": "minor"},
            {"id": "4", "text": "mail me at bob@example.com", "label": None},
        ]
        result = analyze_text_dataset(records, min_words=3, imbalance_threshold=2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["analyzer"], "text")
        self.assertEqual(result["dataset"], {"rows": 4, "columns": 1})
        self.assertIn("health", result)
        self.assertIn("recommendations", result)
        self.assertEqual(result["summary"]["statistics"]["label_distribution"], {"major": 2, "minor": 1})
        self.assertTrue({item["issue_type"] for item in result["findings"]} >= {"empty_text", "possible_short_text", "possible_pii"})


    def test_analyzer_path_and_config(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as folder:
            source = Path(folder) / "docs"
            source.mkdir()
            (source / "a.txt").write_text("A useful text document here.", encoding="utf-8")
            result = analyze_text_dataset(source, health_config=TextHealthScoreConfig())
            self.assertEqual(result["summary"]["statistics"]["document_count"], 1)
            self.assertEqual(result["health"]["grade"], "Excellent")
