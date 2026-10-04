"""Optional embedding-based semantic consistency diagnostics.

No model is downloaded or selected implicitly. Supply an embedding backend
with ``embed_images(paths)`` and ``embed_texts(prompts)`` methods. Similarity
is a model score, not a calibrated probability or a definitive label.
"""

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol

import numpy as np

from ..core.result import Finding


class EmbeddingBackend(Protocol):
    def embed_images(self, image_paths: Sequence[str]) -> Sequence[Sequence[float]]: ...
    def embed_texts(self, prompts: Sequence[str]) -> Sequence[Sequence[float]]: ...


def analyze_semantics(
    records: list[dict],
    root: str | Path,
    expected_domain: str | None = None,
    class_descriptions: Mapping[str, str] | None = None,
    backend: EmbeddingBackend | None = None,
    *,
    domain_similarity_threshold: float = 0.20,
    class_similarity_threshold: float = 0.20,
) -> tuple[dict, list[Finding]]:
    """Compare readable images to domain/class prompts using injected embeddings.

    Scores are cosine similarity in [-1, 1]. Thresholds are configurable and
    are model-specific heuristics; callers should validate them on their data.
    """
    if not -1 <= domain_similarity_threshold <= 1 or not -1 <= class_similarity_threshold <= 1:
        raise ValueError("Similarity thresholds must be between -1 and 1")
    if not expected_domain and not class_descriptions:
        return {"status": "not_requested", "images_checked": 0,
                "message": "Provide expected_domain or class_descriptions to enable semantic checks."}, []
    if backend is None:
        return {"status": "unavailable", "images_checked": 0,
                "message": "Semantic checks require a configured image/text embedding backend; none was supplied."}, []

    readable = [record for record in records if record.get("readable")]
    if not readable:
        return {"status": "completed", "images_checked": 0, "semantic_outliers": 0,
                "message": "No readable images were available for semantic analysis."}, []

    root = Path(root)
    image_paths = [str(record["path"]) for record in readable]
    image_vectors = _normalize(backend.embed_images(image_paths), expected_rows=len(readable), name="image")
    prompts: list[str] = []
    comparisons_by_image: list[list[tuple[str, str, int]]] = []
    class_for_index: list[str | None] = []
    for record in readable:
        path = Path(record["path"])
        relative = path.relative_to(root) if root.is_dir() else Path(path.name)
        label = relative.parts[0] if len(relative.parts) > 1 else None
        class_for_index.append(label)
        comparisons: list[tuple[str, str, int]] = []
        if expected_domain:
            prompt_index = len(prompts)
            prompts.append(f"An image from the {expected_domain} domain")
            comparisons.append(("domain", expected_domain, prompt_index))
        if label and class_descriptions and label in class_descriptions:
            prompt_index = len(prompts)
            prompts.append(class_descriptions[label])
            comparisons.append(("class", label, prompt_index))
        comparisons_by_image.append(comparisons)
    if not prompts:
        return {"status": "completed", "images_checked": len(readable), "semantic_outliers": 0,
                "message": "No applicable domain or class prompts were available for the image paths."}, []

    text_vectors = _normalize(backend.embed_texts(prompts), expected_rows=len(prompts), name="text")
    if image_vectors.shape[1] != text_vectors.shape[1]:
        raise ValueError("Image and text embeddings must have the same vector dimension")

    findings = []
    checks = []
    for index, record in enumerate(readable):
        expected = []
        for kind, label, prompt_index in comparisons_by_image[index]:
            score = float(np.dot(image_vectors[index], text_vectors[prompt_index]))
            threshold = domain_similarity_threshold if kind == "domain" else class_similarity_threshold
            item = {"check": kind, "expected": label, "similarity": round(score, 4), "threshold": threshold}
            expected.append(item)
            if score < threshold:
                expected_text = label
                issue_scope = "dataset domain" if kind == "domain" else "expected class"
                findings.append(Finding(
                    analyzer="image_semantics", issue_type="semantic_outlier", severity="high",
                    message=f"Image may be semantically inconsistent with the expected {issue_scope}; manual review is recommended.",
                    score_impact=5.0, metadata={
                        "file": record["path"], "class": class_for_index[index],
                        "expected_domain": expected_domain, "expected_concept": expected_text,
                        "check": kind, "similarity": round(score, 4), "threshold": threshold,
                        "model_score_is_calibrated_confidence": False,
                    },
                ))
        checks.append({"file": record["path"], "class": class_for_index[index], "comparisons": expected})
    return {"status": "completed", "images_checked": len(readable),
            "semantic_outliers": len(findings), "similarity_metric": "cosine_similarity",
            "thresholds": {"domain": domain_similarity_threshold, "class": class_similarity_threshold},
            "checks": checks,
            "notice": "Similarity scores are model-dependent heuristics, not calibrated confidence or definitive labels."}, findings


def _normalize(values, expected_rows: int, name: str) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != expected_rows or matrix.shape[1] == 0:
        raise ValueError(f"{name} embeddings must be a non-empty 2D matrix with {expected_rows} rows")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} embeddings contain NaN or infinite values")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError(f"{name} embeddings cannot contain zero vectors")
    return matrix / norms
