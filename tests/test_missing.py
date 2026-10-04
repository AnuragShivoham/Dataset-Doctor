import unittest

import pandas as pd

from ml_engine.tabular.missing_values import analyze_missing_values


class MissingTests(unittest.TestCase):
    def test_clean_and_missing_data(self):
        clean = analyze_missing_values(pd.DataFrame({"x": [1, 2]}))
        self.assertEqual(clean[0]["total_missing_cells"], 0)
        data, findings, _ = analyze_missing_values(pd.DataFrame({"x": [1, None]}))
        self.assertEqual(data["total_missing_cells"], 1)
        self.assertEqual(findings[0].issue_type, "missing_values")
