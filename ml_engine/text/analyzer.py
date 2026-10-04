"""Orchestrate read-only text dataset diagnostics."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.result import AnalysisResult, Finding
from ..recommendations.rule_engine import generate_recommendations
from ..scoring.health_score import calculate_health_score
from .distribution import analyze_distribution
from .duplicates import analyze_duplicates
from .loader import TextRecord, load_text_dataset
from .pii import analyze_pii
from .quality import analyze_quality
from .statistics import analyze_statistics


@dataclass(frozen=True)
class TextHealthScoreConfig:
    """Text health score weights; weights are normalized when scoring."""

    completeness_weight: float = 0.30
    validity_weight: float = 0.10
    consistency_weight: float = 0.10
    duplicate_weight: float = 0.15
    outlier_weight: float = 0.10
    balance_weight: float = 0.10
    leakage_weight: float = 0.15

    def as_health_config(self):
        from ..scoring.health_score import HealthScoreConfig
        return HealthScoreConfig(
            completeness_weight=self.completeness_weight,
            validity_weight=self.validity_weight,
            consistency_weight=self.consistency_weight,
            duplicate_weight=self.duplicate_weight,
            outlier_weight=self.outlier_weight,
            balance_weight=self.balance_weight,
            leakage_weight=self.leakage_weight,
        )


def analyze_text_dataset(
    source: str | Path | list[dict[str, Any] | TextRecord],
    *,
    text_column: str = "text",
    id_column: str = "id",
    label_column: str = "label",
    min_words: int = 3,
    max_words: int = 1000,
    imbalance_threshold: float = 3.0,
    health_config: TextHealthScoreConfig | None = None,
) -> dict:
    """Analyze a text corpus without modifying the source data."""
    if isinstance(source, (str, Path)):
        loaded = load_text_dataset(source, text_column=text_column, id_column=id_column,
                                   label_column=label_column)
        records = [dict(item) for item in loaded]
    elif isinstance(source, list):
        records = [_as_record(item, index) for index, item in enumerate(source)]
    else:
        raise TypeError("source must be a path or a list of text records")

    statistics = analyze_statistics(records, min_words=min_words, max_words=max_words)
    quality, findings = analyze_quality(records, min_words=min_words, max_words=max_words)
    duplicates, duplicate_findings = analyze_duplicates(records)
    distribution, distribution_findings = analyze_distribution(records, imbalance_threshold=imbalance_threshold)
    pii, pii_findings = analyze_pii(records)
    findings.extend(duplicate_findings)
    findings.extend(distribution_findings)
    findings.extend(pii_findings)

    row_count = len(records)
    profile = {
        "rows": row_count,
        "columns": 1,
        "documents": row_count,
        "labeled_documents": row_count - statistics["unlabeled_documents"],
        "unlabeled_documents": statistics["unlabeled_documents"],
    }
    health = calculate_health_score(
        {"rows": row_count, "columns": 1, "missing_cells": quality["empty_documents"],
         "duplicate_rows": duplicates["duplicate_documents"]},
        findings,
        config=health_config.as_health_config() if health_config else None,
    )
    summary = {"statistics": statistics, "quality": quality, "duplicates": duplicates,
               "distribution": distribution, "privacy": pii, "health": health}
    return AnalysisResult("text", "completed", summary, findings,
                          generate_recommendations(findings)).to_dict() | {
                              "dataset": {"rows": row_count, "columns": 1},
                              "profile": profile,
                              "health": health,
                          }


def _as_record(record: dict[str, Any] | TextRecord, index: int) -> dict[str, Any]:
    if isinstance(record, TextRecord):
        return {"id": record.record_id, "text": record.text, "label": record.label}
    if not isinstance(record, dict):
        raise TypeError(f"record {index} must be a dict or TextRecord")
    if "text" not in record:
        raise ValueError(f"record {index} does not contain a 'text' field")
    return {"id": str(record.get("id", index)), "text": "" if record["text"] is None else str(record["text"]),
            "label": None if record.get("label") is None else str(record["label"])}
