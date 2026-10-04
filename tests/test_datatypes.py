import unittest

import pandas as pd

from ml_engine.tabular.datatypes import analyze_datatypes


class DatatypeTests(unittest.TestCase):
    def test_numeric_text_with_inconsistent_value(self):
        _, findings, _ = analyze_datatypes(pd.DataFrame({"age": ["22", "25", "thirty", "31"]}))
        self.assertEqual(findings[0].issue_type, "type_inconsistency")

    def test_consistent_text_not_flagged(self):
        _, findings, _ = analyze_datatypes(pd.DataFrame({"city": ["Delhi", "Pune", "Delhi"]}))
        self.assertFalse(findings)
