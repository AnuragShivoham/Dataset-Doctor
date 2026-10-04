"""Orchestrate the initial tabular quality analysis."""

from pathlib import Path

import pandas as pd

from ..core.result import AnalysisResult
from ..recommendations.rule_engine import generate_recommendations
from ..scoring.health_score import calculate_health_score
from .duplicates import analyze_duplicates
from .datatypes import analyze_datatypes
from .imbalance import analyze_imbalance
from .leakage import analyze_leakage
from .loader import load_tabular_dataset
from .missing_values import analyze_missing_values
from .outliers import analyze_outliers
from .profiler import profile_columns, profile_dataset


def analyze_tabular(data: pd.DataFrame | str | Path, target_column: str | None = None) -> dict:
    """Analyze a DataFrame or CSV/Excel path and return JSON-ready results."""
    df = load_tabular_dataset(data) if isinstance(data, (str, Path)) else data
    if not isinstance(df, pd.DataFrame):
        raise TypeError("data must be a pandas DataFrame or a supported file path")
    if df.columns.has_duplicates:
        duplicate_names = df.columns[df.columns.duplicated()].tolist()
        raise ValueError(f"Dataset contains duplicate column names: {duplicate_names}")

    summary = {"profile": profile_dataset(df), "columns": profile_columns(df)}
    findings = []
    analyzers = {
        "missing_values": lambda: analyze_missing_values(df),
        "duplicates": lambda: analyze_duplicates(df),
        "outliers": lambda: analyze_outliers(df, {target_column} if target_column else None),
        "datatypes": lambda: analyze_datatypes(df),
        "leakage": lambda: analyze_leakage(df, target_column),
    }
    if target_column is not None:
        analyzers["imbalance"] = lambda: analyze_imbalance(df, target_column)
    for name, analyzer in analyzers.items():
        details, new_findings, new_recommendations = analyzer()
        summary[name] = details
        findings.extend(new_findings)
    recommendations = generate_recommendations(findings)
    health = calculate_health_score(summary["profile"], findings)
    dataset = {"rows": summary["profile"]["rows"], "columns": summary["profile"]["columns"]}
    return AnalysisResult(
        analyzer="tabular",
        status="completed",
        summary={**summary, "health": health},
        findings=findings,
        recommendations=recommendations,
    ).to_dict() | {"dataset": dataset, "profile": summary["profile"], "health": health}
