import json
import unittest

from ml_engine.text.loader import TextDatasetError, TextRecord, load_text_dataset


class TextLoaderTests(unittest.TestCase):
    def test_load_txt_and_textrecord(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            path = Path(folder) / "sample.txt"
            path.write_text("This is a text document.", encoding="utf-8")
            self.assertEqual(load_text_dataset(path)[0]["text"], "This is a text document.")
            record = load_text_dataset(path, as_records=True)[0]
            self.assertIsInstance(record, TextRecord)
            self.assertEqual(record.record_id, "sample.txt")
            self.assertEqual(record.metadata["extension"], ".txt")


    def test_load_directory_and_infer_labels(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "positive").mkdir()
            (root / "negative").mkdir()
            (root / "positive" / "one.txt").write_text("This is good.", encoding="utf-8")
            (root / "negative" / "two.txt").write_text("This is bad.", encoding="utf-8")
            records = load_text_dataset(root)
            self.assertEqual({record["label"] for record in records}, {"positive", "negative"})


    def test_load_csv_json_and_jsonl(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            root = Path(folder)
            csv_file = root / "reviews.csv"
            csv_file.write_text('id,text,label\n1,"Excellent product",positive\n', encoding="utf-8")
            self.assertEqual(load_text_dataset(csv_file)[0]["text"], "Excellent product")
            json_file = root / "data.json"
            json_file.write_text(json.dumps([{"text": "Hello", "label": "x"}]), encoding="utf-8")
            self.assertEqual(load_text_dataset(json_file)[0]["text"], "Hello")
            jsonl_file = root / "data.jsonl"
            jsonl_file.write_text('{"id": 2, "text": "World"}\n', encoding="utf-8")
            self.assertEqual(load_text_dataset(jsonl_file)[0]["id"], "2")


    def test_invalid_paths_formats_and_records_raise_domain_error(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(TextDatasetError):
                load_text_dataset(root / "missing.txt")
            unsupported = root / "data.xml"
            unsupported.write_text("<text/>", encoding="utf-8")
            with self.assertRaises(TextDatasetError):
                load_text_dataset(unsupported)
            invalid_json = root / "bad.json"
            invalid_json.write_text("{bad", encoding="utf-8")
            with self.assertRaises(TextDatasetError):
                load_text_dataset(invalid_json)


    def test_custom_text_column_and_empty_directory(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "custom.csv"
            path.write_text("body,category\nHello,news\n", encoding="utf-8")
            self.assertEqual(load_text_dataset(path, text_column="body", label_column="category")[0]["label"], "news")
            with self.assertRaises(TextDatasetError):
                load_text_dataset(root)


from pathlib import Path
