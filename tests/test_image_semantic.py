import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ml_engine import analyze_image_dataset
from ml_engine.image.loader import inspect_image
from ml_engine.image.semantic import analyze_semantics


class FakeEmbeddingBackend:
    def __init__(self, image_vectors):
        self.image_vectors = image_vectors

    def embed_images(self, image_paths):
        return [self.image_vectors[Path(path).name] for path in image_paths]

    def embed_texts(self, prompts):
        return [[1.0, 0.0] for _ in prompts]


class ImageSemanticTests(unittest.TestCase):
    def test_checks_skipped_when_not_requested_or_backend_missing(self):
        record = {"path": "fracture/x.png", "readable": True}
        result, findings = analyze_semantics([record], "fracture")
        self.assertEqual(result["status"], "not_requested")
        self.assertFalse(findings)
        result, findings = analyze_semantics([record], "fracture", expected_domain="bone X-ray")
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(findings)

    def test_domain_and_class_semantic_outliers_are_review_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            class_dir = root / "fracture"
            class_dir.mkdir()
            good = class_dir / "xray.png"
            suspicious = class_dir / "flower.png"
            Image.new("RGB", (80, 80), "gray").save(good)
            Image.new("RGB", (80, 80), "pink").save(suspicious)
            records = [inspect_image(good), inspect_image(suspicious)]
            backend = FakeEmbeddingBackend({"xray.png": [1.0, 0.0], "flower.png": [0.0, 1.0]})
            result, findings = analyze_semantics(
                records, root, "bone X-ray",
                {"fracture": "a bone X-ray showing a fracture"}, backend,
            )
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["semantic_outliers"], 2)
            self.assertTrue(all(item.issue_type == "semantic_outlier" for item in findings))
            self.assertTrue(all(item.metadata["model_score_is_calibrated_confidence"] is False for item in findings))
            self.assertEqual({item.metadata["file"] for item in findings}, {str(suspicious)})

    def test_public_analyzer_adds_semantic_status_and_recommendation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            class_dir = root / "fracture"
            class_dir.mkdir()
            path = class_dir / "sample.png"
            Image.new("RGB", (80, 80), "purple").save(path)
            result = analyze_image_dataset(
                root, expected_domain="bone X-ray",
                semantic_backend=FakeEmbeddingBackend({"sample.png": [0.0, 1.0]}),
            )
            self.assertEqual(result["summary"]["semantic"]["semantic_outliers"], 1)
            self.assertTrue(any(item["category"] == "data_review" for item in result["recommendations"]))
