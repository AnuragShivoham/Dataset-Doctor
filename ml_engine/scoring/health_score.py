"""Explainable, size-aware dataset health score.

Grade cutoffs are application labels, not scientific standards. Component
weights and thresholds can be customized with ``HealthScoreConfig``.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math

from ..core.result import Finding

GRADE_CUTOFFS = ((90, "Excellent"), (75, "Good"), (60, "Fair"), (40, "Poor"), (0, "Critical"))


@dataclass(frozen=True)
class HealthScoreConfig:
    completeness_weight: float = 0.20
    validity_weight: float = 0.20
    consistency_weight: float = 0.15
    duplicate_weight: float = 0.10
    outlier_weight: float = 0.10
    balance_weight: float = 0.10
    leakage_weight: float = 0.15

    def weights(self) -> dict[str, float]:
        weights = {
            "completeness": self.completeness_weight, "validity": self.validity_weight,
            "consistency": self.consistency_weight, "duplicates": self.duplicate_weight,
            "outliers": self.outlier_weight, "balance": self.balance_weight,
            "leakage": self.leakage_weight,
        }
        if any(value < 0 for value in weights.values()) or sum(weights.values()) <= 0:
            raise ValueError("Health score weights must be non-negative and sum to more than zero")
        return weights


def calculate_health_score(
    profile: Mapping | None = None,
    findings: Iterable[Finding | Mapping] = (),
    config: HealthScoreConfig | None = None,
) -> dict:
    """Score quality components from profile prevalence and standardized findings."""
    profile = profile or {}
    findings = [_finding_dict(item) for item in findings]
    config = config or HealthScoreConfig()
    profile_rows = int(profile.get("rows", 0) or 0)
    columns = int(profile.get("columns", 0) or 0)
    total_cells = profile_rows * columns
    missing_cells = int(profile.get("missing_cells", 0) or 0)
    missing_pct = min(100.0, missing_cells / total_cells * 100) if total_cells else 0.0
    duplicate_count = int(profile.get("duplicate_rows", 0) or 0)
    duplicate_pct = min(100.0, duplicate_count / profile_rows * 100) if profile_rows else 0.0

    def component_for(issue_types: set[str], prevalence_key: str | None = None, factor: float = 1.0, default: float = 100.0) -> float:
        relevant = [item for item in findings if item.get("issue_type") in issue_types]
        if not relevant:
            return default
        rates = [float((item.get("metadata") or {}).get(prevalence_key, 0) or 0) for item in relevant] if prevalence_key else []
        if rates:
            penalty = min(100.0, max(rates) * factor)
        else:
            penalty = min(100.0, sum(_severity_penalty(item.get("severity", "low")) for item in relevant))
        return round(max(0.0, 100.0 - penalty), 1)

    balance_findings = [item for item in findings if item.get("issue_type") == "class_imbalance"]
    if balance_findings:
        ratio = float((balance_findings[0].get("metadata") or {}).get("imbalance_ratio", 1.0) or 1.0)
        balance_score = 100.0 * (1.0 - min(1.0, max(0.0, math.log10(max(1.0, ratio)) / 2.0)))
    else:
        balance_score = 100.0

    components = {
        "completeness": round(max(0.0, 100.0 - missing_pct * 2.0), 1),
        "validity": component_for({"invalid_values", "invalid_format", "invalid_range", "corrupt_image", "zero_byte_file", "unsupported_image_format", "invalid_dimensions"}),
        "consistency": component_for({"type_inconsistency", "inconsistent_values", "possible_blur", "brightness_anomaly", "extreme_aspect_ratio", "low_resolution", "semantic_outlier"}),
        "duplicates": component_for({"duplicate_rows", "duplicate_image"}, "duplicate_percentage", 2.0) if any(item.get("issue_type") in {"duplicate_rows", "duplicate_image"} for item in findings) else round(max(0.0, 100.0 - duplicate_pct * 2.0), 1),
        "outliers": component_for({"outliers"}, "outlier_percentage", 2.0),
        "balance": round(balance_score, 1),
        "leakage": component_for({"possible_data_leakage", "suspicious_target_relationship"}),
    }
    weights = config.weights()
    weight_sum = sum(weights.values())
    score = round(sum(components[key] * weight for key, weight in weights.items()) / weight_sum, 1)
    grade = next(label for cutoff, label in GRADE_CUTOFFS if score >= cutoff)
    return {"score": score, "grade": grade, "components": components,
            "weights": {key: round(value / weight_sum, 4) for key, value in weights.items()}}


def _finding_dict(item: Finding | Mapping) -> dict:
    if isinstance(item, Finding):
        return {"issue_type": item.issue_type, "severity": item.severity, "metadata": item.metadata}
    return dict(item)


def _severity_penalty(severity: str) -> float:
    return {"low": 5.0, "medium": 10.0, "high": 20.0, "critical": 35.0}.get(str(severity).lower(), 5.0)
