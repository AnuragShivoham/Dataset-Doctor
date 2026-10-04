import unittest

import pandas as pd

from ml_engine.tabular.duplicates import analyze_duplicates


class DuplicateTests(unittest.TestCase):
    def test_duplicate_count(self):
        summary, findings, _ = analyze_duplicates(pd.DataFrame({"x": [1, 1, 2]}))
        self.assertEqual(summary["duplicate_rows"], 1)
        self.assertEqual(findings[0].issue_type, "duplicate_rows")

    def test_no_duplicates(self):
        summary, findings, _ = analyze_duplicates(pd.DataFrame({"x": [1, 2]}))
        self.assertEqual(summary["duplicate_rows"], 0)
        self.assertFalse(findings)
