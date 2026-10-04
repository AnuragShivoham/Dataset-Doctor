"""Heuristics for possible identifiers and unusually target-associated features."""

import re

import pandas as pd

from ..core.result import Finding

IDENTIFIER_TOKEN = re.compile(r"(^|_)(id|uuid|guid|key|index)($|_)", re.IGNORECASE)


def analyze_leakage(df: pd.DataFrame, target_column: str | None = None) -> tuple[dict, list[Finding], list[str]]:
    if target_column is not None and target_column not in df.columns:
        raise ValueError(f"Target column not found: {target_column}")
    rows = len(df)
    findings, recommendations, columns = [], [], []
    for column in df.columns:
        if column == target_column:
            continue
        series = df[column]
        unique_ratio = float(series.nunique(dropna=True) / rows) if rows else 0.0
        normalized = re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        identifier_name = bool(IDENTIFIER_TOKEN.search(normalized))
        identifier_like = identifier_name or (rows >= 20 and unique_ratio >= 0.98)
        columns.append({"column": str(column), "unique_ratio": round(unique_ratio, 4),
                        "identifier_like": identifier_like, "identifier_name_match": identifier_name})
        if identifier_like:
            why = "identifier-like name" if identifier_name else f"near-unique values ({unique_ratio:.1%})"
            findings.append(Finding(
                analyzer="leakage", issue_type="possible_data_leakage", severity="high",
                message=f"Column appears identifier-like ({why}) and should be reviewed for potential leakage.",
                score_impact=5.0, column=str(column),
                metadata={"unique_ratio": round(unique_ratio, 4), "heuristic": why},
            ))
            recommendations.append(f"Check whether {column} is available at prediction time and whether it encodes record or target information.")

    suspicious = []
    if target_column is not None:
        target = df[target_column]
        for column in df.columns:
            if column == target_column:
                continue
            pair = df[[column, target_column]].dropna()
            if len(pair) < 3 or pair[column].nunique() < 2 or pair[target_column].nunique() < 2:
                continue
            association = None
            if pd.api.types.is_numeric_dtype(pair[column]) and pd.api.types.is_numeric_dtype(pair[target_column]):
                value = pair[column].corr(pair[target_column])
                association = abs(float(value)) if pd.notna(value) else None
                metric = "absolute_pearson_correlation"
            else:
                # A feature that almost uniquely determines target labels is a warning heuristic.
                rates = pair.groupby(column, dropna=False)[target_column].nunique()
                association = float((rates <= 1).mean())
                metric = "single_class_group_fraction"
            if association is not None and association >= 0.98:
                suspicious.append({"column": str(column), "metric": metric, "value": round(association, 4)})
                findings.append(Finding(
                    analyzer="leakage", issue_type="suspicious_target_relationship", severity="high",
                    message=f"{column} has an unusually strong relationship with target {target_column}; investigate possible leakage.",
                    score_impact=5.0, column=str(column),
                    metadata={"target_column": str(target_column), "metric": metric, "association": round(association, 4)},
                ))
                recommendations.append(f"Verify that {column} is a legitimate pre-outcome feature and is not derived from {target_column}.")
    return {"target_column": target_column, "columns": columns, "suspicious_target_relationships": suspicious}, findings, recommendations
