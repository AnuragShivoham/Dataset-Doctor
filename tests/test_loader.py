import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ml_engine.tabular.loader import load_tabular_dataset


class LoaderTests(unittest.TestCase):
    def test_csv_and_excel_load(self):
        with tempfile.TemporaryDirectory() as folder:
            csv_path = Path(folder) / "data.csv"
            xlsx_path = Path(folder) / "data.xlsx"
            frame = pd.DataFrame({"x": [1, 2]})
            frame.to_csv(csv_path, index=False)
            frame.to_excel(xlsx_path, index=False)
            self.assertEqual(load_tabular_dataset(csv_path).shape, (2, 1))
            self.assertEqual(load_tabular_dataset(xlsx_path).shape, (2, 1))

    def test_invalid_path_and_extension(self):
        with self.assertRaises(FileNotFoundError):
            load_tabular_dataset("does-not-exist.csv")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "data.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_tabular_dataset(path)
