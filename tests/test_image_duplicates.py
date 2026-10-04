import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine.image.loader import inspect_image
from ml_engine.image.duplicates import analyze_duplicates


class ImageDuplicateTests(unittest.TestCase):
    def test_exact_duplicate_and_no_duplicate(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second, unique = (Path(folder) / name for name in ("a.png", "b.png", "c.png"))
            Image.new("RGB", (10, 10), "red").save(first)
            second.write_bytes(first.read_bytes())
            Image.new("RGB", (10, 10), "blue").save(unique)
            records = [inspect_image(path) for path in (first, second, unique)]
            summary, findings = analyze_duplicates(records)
            self.assertEqual(summary["duplicate_groups"], 1)
            self.assertEqual(len(findings), 1)
            summary, findings = analyze_duplicates([records[-1]])
            self.assertEqual(summary["duplicate_groups"], 0)
            self.assertFalse(findings)
