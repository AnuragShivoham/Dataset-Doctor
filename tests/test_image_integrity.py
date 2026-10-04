import unittest

from ml_engine.image.integrity import analyze_integrity


class ImageIntegrityTests(unittest.TestCase):
    def test_corrupt_zero_byte_and_unsupported_findings(self):
        records = [
            {"path": "bad.jpg", "filename": "bad.jpg", "error": "decode_error"},
            {"path": "empty.png", "filename": "empty.png", "error": "zero_byte"},
        ]
        summary, findings = analyze_integrity(records, ["file.gif"])
        self.assertEqual(summary["corrupt_images"], 1)
        self.assertEqual(summary["zero_byte_files"], 1)
        self.assertEqual(summary["unsupported_files"], 1)
        self.assertEqual(len(findings), 3)
