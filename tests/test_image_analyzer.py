import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine import analyze_image_dataset


class ImageAnalyzerTests(unittest.TestCase):
    def test_complete_analysis_contract_and_read_only_behavior(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "cats").mkdir()
            path = root / "cats" / "one.png"
            Image.new("RGB", (100, 100), "green").save(path)
            original = path.read_bytes()
            result = analyze_image_dataset(root)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["dataset"]["rows"], 1)
            self.assertIn("health", result)
            self.assertIn("findings", result)
            self.assertIn("recommendations", result)
            self.assertEqual(path.read_bytes(), original)
