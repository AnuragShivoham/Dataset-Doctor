import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine.image.loader import inspect_image
from ml_engine.image.distribution import analyze_distribution


class ImageDistributionTests(unittest.TestCase):
    def test_balanced_and_imbalanced_classes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for label, count in (("cats", 2), ("dogs", 2)):
                directory = root / label
                directory.mkdir()
                for index in range(count):
                    path = directory / f"{index}.png"
                    Image.new("RGB", (80, 80), (index, 0, 0)).save(path)
                    paths.append(path)
            summary, findings = analyze_distribution([inspect_image(path) for path in paths], root)
            self.assertEqual(summary["classes"], {"cats": 2, "dogs": 2})
            self.assertEqual(summary["status"], "healthy")
            self.assertFalse(findings)

            path = root / "cats" / "2.png"
            Image.new("RGB", (80, 80), "red").save(path)
            paths.append(path)
            summary, findings = analyze_distribution([inspect_image(item) for item in paths], root)
            self.assertEqual(summary["imbalance_ratio"], 1.5)
            self.assertFalse(findings)

    def test_warning_at_three_to_one(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for label, count in (("major", 3), ("minor", 1)):
                directory = root / label
                directory.mkdir()
                for index in range(count):
                    path = directory / f"{index}.png"
                    Image.new("RGB", (80, 80), (index, 20, 20)).save(path)
                    paths.append(path)
            summary, findings = analyze_distribution([inspect_image(item) for item in paths], root)
            self.assertEqual(summary["status"], "imbalanced")
            self.assertEqual(summary["minority_class"], "minor")
            self.assertEqual(len(findings), 1)
