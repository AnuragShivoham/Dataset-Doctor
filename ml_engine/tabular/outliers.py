"""IQR-based outlier diagnostics for numeric columns (no rows are changed)."""

import pandas as pd

from ..core.result import Finding


def analyze_outliers(df: pd.DataFrame, exclude_columns: set[str] | None = None) -> tuple[dict, list[Finding], list[str]]:
    columns = []
    findings = []
    recommendations = []
    numeric = df.select_dtypes(include=["number"])
    if exclude_columns:
        numeric = numeric.drop(columns=list(exclude_columns), errors="ignore")
    for column in numeric.columns:
        values = numeric[column].dropna()
        if values.empty:
            continue
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((values < lower) | (values > upper)).sum())
        percentage = count / len(values) * 100
        columns.append({
            "column": str(column), "outlier_count": count,
            "outlier_percentage": round(percentage, 2), "method": "IQR",
            "lower_bound": lower, "upper_bound": upper,
        })
        if count:
            severity = "low" if percentage < 1 else "medium" if percentage <= 5 else "high"
            findings.append(Finding(
                analyzer="outliers", issue_type="outliers", severity=severity,
                message=f"{column} has {count} IQR outliers ({percentage:.2f}% of non-missing values).",
                score_impact=min(10.0, percentage * 0.1), column=str(column),
                metadata={"outlier_count": count, "outlier_percentage": round(percentage, 2),
                          "method": "IQR", "lower_bound": lower, "upper_bound": upper},
            ))
            recommendations.append(f"Review unusual values in {column}; do not remove them without checking whether they are valid observations.")
    return {"method": "IQR", "columns": columns}, findings, recommendations
