import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine import analyze_image_dataset, analyze_tabular, analyze_text_dataset


class PublicAnalyzerContractTests(unittest.TestCase):
    def _assert_contract(self, result):
        self.assertEqual(result["status"], "completed")
        for key in ("dataset", "profile", "health", "findings", "recommendations"):
            self.assertIn(key, result)

    def test_all_modalities_share_top_level_contract(self):
        self._assert_contract(analyze_tabular("sample-data/test.csv", target_column="Target"))
        self._assert_contract(analyze_text_dataset([{"id": "1", "text": "A small text sample."}]))
        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "one.png"
            Image.new("RGB", (8, 8), "blue").save(image_path)
            self._assert_contract(analyze_image_dataset(image_path))


if __name__ == "__main__":
    unittest.main()
