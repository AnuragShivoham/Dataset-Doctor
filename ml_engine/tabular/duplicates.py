"""Duplicate-row diagnostics."""

import pandas as pd

from ..core.result import Finding


def analyze_duplicates(df: pd.DataFrame) -> tuple[dict, list[Finding], list[str]]:
    count = int(df.duplicated().sum())
    percentage = (count / len(df) * 100) if len(df) else 0.0
    findings = []
    recommendations = []
    if count:
        severity = "high" if percentage >= 20 else "medium" if percentage >= 5 else "low"
        findings.append(Finding(
            analyzer="duplicates",
            issue_type="duplicate_rows",
            severity=severity,
            message=f"{count} duplicate rows found ({percentage:.1f}% of rows)",
            score_impact=round(min(10.0, percentage * 0.1), 2),
            metadata={"duplicate_rows": count, "duplicate_percentage": round(percentage, 2)},
        ))
        recommendations.append("Review duplicate rows and confirm whether they represent repeated records or valid repeated observations.")
    return {"duplicate_rows": count, "duplicate_percentage": round(percentage, 2)}, findings, recommendations
