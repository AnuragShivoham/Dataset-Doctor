"""Target class distribution diagnostics. The target must be supplied explicitly."""

import pandas as pd

from ..core.result import Finding


def analyze_imbalance(df: pd.DataFrame, target_column: str) -> tuple[dict, list[Finding], list[str]]:
    if target_column not in df.columns:
        raise ValueError(f"Target column not found: {target_column}")
    counts = df[target_column].value_counts(dropna=False)
    non_null_counts = df[target_column].value_counts(dropna=True)
    total = int(non_null_counts.sum())
    classes = [{"class": _safe_scalar(label), "count": int(count),
                "percentage": round(int(count) / total * 100, 2) if total else 0.0}
               for label, count in non_null_counts.items()]
    missing_target = int(df[target_column].isna().sum())
    if len(non_null_counts) < 2:
        return {"target_column": str(target_column), "class_counts": classes,
                "status": "not_assessed",
                "missing_target_count": missing_target, "minority_class": None,
                "majority_class": classes[0]["class"] if classes else None,
                "imbalance_ratio": None}, [], []
    minority_label, minority_count = non_null_counts.idxmin(), int(non_null_counts.min())
    majority_label, majority_count = non_null_counts.idxmax(), int(non_null_counts.max())
    ratio = majority_count / minority_count if minority_count else None
    has_minority_tie = int((non_null_counts == minority_count).sum()) > 1
    has_majority_tie = int((non_null_counts == majority_count).sum()) > 1
    summary = {"target_column": str(target_column), "class_counts": classes,
               "status": "healthy" if ratio < 3 else "imbalanced",
               "missing_target_count": missing_target,
               "minority_class": None if has_minority_tie else _safe_scalar(minority_label),
               "majority_class": None if has_majority_tie else _safe_scalar(majority_label),
               "imbalance_ratio": round(ratio, 4) if ratio is not None else None}
    findings, recommendations = [], []
    if ratio is not None and ratio >= 3:
        severity = "high" if ratio >= 10 else "medium"
        findings.append(Finding(
            analyzer="imbalance", issue_type="class_imbalance", severity=severity,
            message=f"Target {target_column} has a majority-to-minority class ratio of {ratio:.2f}:1.",
            score_impact=min(10.0, ratio), column=str(target_column), metadata=summary,
        ))
        recommendations.append("Consider class weighting or resampling during model training; this analysis does not alter the dataset.")
    return summary, findings, recommendations


def _safe_scalar(value):
    return value.item() if hasattr(value, "item") else value
