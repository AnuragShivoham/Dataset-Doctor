import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine.image.loader import discover_images, inspect_image


class ImageLoaderTests(unittest.TestCase):
    def test_supported_discovery_and_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ok.PNG"
            Image.new("RGB", (20, 30)).save(path)
            supported, unsupported = discover_images(folder)
            record = inspect_image(supported[0])
            self.assertFalse(unsupported)
            self.assertEqual((record["width"], record["height"], record["channels"]), (20, 30, 3))
            self.assertTrue(record["readable"])

    def test_corrupt_and_zero_byte_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            corrupt = Path(folder) / "bad.jpg"
            empty = Path(folder) / "empty.png"
            corrupt.write_bytes(b"not an image")
            empty.write_bytes(b"")
            self.assertEqual(inspect_image(corrupt)["error"], "decode_error")
            self.assertEqual(inspect_image(empty)["error"], "zero_byte")

    def test_unsupported_extension_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "note.txt"
            path.write_text("x", encoding="utf-8")
            supported, unsupported = discover_images(folder)
            self.assertFalse(supported)
            self.assertEqual(unsupported, [path])
