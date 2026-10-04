"""Missing-value diagnostics."""

import pandas as pd

from ..core.result import Finding


def analyze_missing_values(df: pd.DataFrame) -> tuple[dict, list[Finding], list[str]]:
    counts = df.isna().sum()
    total_missing = int(counts.sum())
    columns = []
    findings = []
    recommendations = []
    row_count = len(df)
    for column, count in counts.items():
        count = int(count)
        if not count:
            continue
        percentage = (count / row_count * 100) if row_count else 0.0
        columns.append({"column": str(column), "missing_count": count, "missing_percentage": round(percentage, 2)})
        severity = "high" if percentage >= 30 else "medium" if percentage >= 10 else "low"
        findings.append(Finding(
            analyzer="missing_values",
            issue_type="missing_values",
            severity=severity,
            message=f"{column} contains {percentage:.1f}% missing values ({count} rows)",
            score_impact=round(min(10.0, percentage * 0.1), 2),
            column=str(column),
            metadata={"missing_count": count, "missing_percentage": round(percentage, 2)},
        ))
        recommendations.append(f"Review missing values in {column}; choose an imputation or removal strategy appropriate to its meaning.")
    return {"total_missing_cells": total_missing, "columns_with_missing": len(columns), "columns": columns}, findings, recommendations
