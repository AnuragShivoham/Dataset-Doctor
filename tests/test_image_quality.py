import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine.image.loader import inspect_image
from ml_engine.image.quality import analyze_quality


class ImageQualityTests(unittest.TestCase):
    def test_tiny_dark_and_blurry_signals(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dark.png"
            Image.new("RGB", (16, 16), (0, 0, 0)).save(path)
            measures, findings = analyze_quality([inspect_image(path)])
            issues = {item.issue_type for item in findings}
            self.assertEqual(len(measures), 1)
            self.assertIn("low_resolution", issues)
            self.assertIn("brightness_anomaly", issues)
            self.assertIn("possible_blur", issues)

    def test_bright_and_extreme_aspect_signals(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bright.png"
            Image.new("RGB", (400, 80), (255, 255, 255)).save(path)
            _, findings = analyze_quality([inspect_image(path)])
            self.assertIn("brightness_anomaly", {item.issue_type for item in findings})
            self.assertIn("extreme_aspect_ratio", {item.issue_type for item in findings})
