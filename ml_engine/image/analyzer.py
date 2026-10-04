"""Orchestrate a read-only image dataset quality analysis."""

from pathlib import Path

from ..core.result import AnalysisResult
from ..recommendations.rule_engine import generate_recommendations
from ..scoring.health_score import calculate_health_score
from .distribution import analyze_distribution
from .duplicates import analyze_duplicates
from .integrity import analyze_integrity
from .loader import discover_images, inspect_image
from .quality import analyze_quality
from .semantic import EmbeddingBackend, analyze_semantics


def analyze_image_dataset(
    source: str | Path,
    *,
    expected_domain: str | None = None,
    class_descriptions: dict[str, str] | None = None,
    semantic_backend: EmbeddingBackend | None = None,
    domain_similarity_threshold: float = 0.20,
    class_similarity_threshold: float = 0.20,
) -> dict:
    """Analyze one image or a directory tree; the source files are never altered."""
    root = Path(source)
    supported, unsupported = discover_images(root)
    records = [inspect_image(path) for path in supported]
    integrity, findings = analyze_integrity(records, [str(path) for path in unsupported])
    quality, quality_findings = analyze_quality(records)
    duplicate_summary, duplicate_findings = analyze_duplicates(records)
    distribution, distribution_findings = analyze_distribution(records, root)
    semantic, semantic_findings = analyze_semantics(
        records, root, expected_domain, class_descriptions, semantic_backend,
        domain_similarity_threshold=domain_similarity_threshold,
        class_similarity_threshold=class_similarity_threshold,
    )
    findings.extend(quality_findings)
    findings.extend(duplicate_findings)
    findings.extend(distribution_findings)
    findings.extend(semantic_findings)

    discovered_count = len(supported) + len(unsupported)
    readable_count = sum(bool(record.get("readable")) for record in records)
    profile = {
        "rows": discovered_count,
        "columns": 1,
        "image_files": len(supported),
        "unsupported_files": len(unsupported),
        "readable_images": readable_count,
        "unreadable_images": len(supported) - readable_count,
        "formats": dict(sorted(_count_formats(records).items())),
    }
    health = calculate_health_score(
        {"rows": discovered_count, "columns": 1,
         "missing_cells": len(supported) - readable_count,
         "duplicate_rows": duplicate_summary["duplicate_files"]}, findings,
    )
    summary = {"integrity": integrity, "quality": quality,
               "duplicates": duplicate_summary, "distribution": distribution,
               "semantic": semantic}
    recommendations = generate_recommendations(findings)
    result = AnalysisResult("image", "completed", {**summary, "health": health}, findings, recommendations).to_dict()
    result.update({"dataset": {"rows": discovered_count, "columns": 1}, "profile": profile, "health": health})
    return result


def _count_formats(records: list[dict]) -> dict[str, int]:
    formats: dict[str, int] = {}
    for record in records:
        extension = record["extension"] or "(none)"
        formats[extension] = formats.get(extension, 0) + 1
    return formats
