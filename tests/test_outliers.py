import unittest

import pandas as pd

from ml_engine.tabular.outliers import analyze_outliers


class OutlierTests(unittest.TestCase):
    def test_outlier_found_and_target_can_be_excluded(self):
        frame = pd.DataFrame({"x": [1, 1, 1, 1, 100], "target": [0, 0, 0, 1, 1]})
        summary, findings, _ = analyze_outliers(frame, {"target"})
        self.assertEqual(summary["columns"][0]["outlier_count"], 1)
        self.assertEqual(findings[0].metadata["method"], "IQR")

    def test_no_outlier(self):
        _, findings, _ = analyze_outliers(pd.DataFrame({"x": [1, 2, 3, 4]}))
        self.assertFalse(findings)
