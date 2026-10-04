"""Dataset-level and per-column profiling helpers."""

import pandas as pd


def profile_dataset(df: pd.DataFrame) -> dict:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "numeric_columns": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical_columns": df.select_dtypes(include=["object", "category", "string"]).columns.tolist(),
        "boolean_columns": df.select_dtypes(include=["bool"]).columns.tolist(),
        "datetime_columns": df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist(),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_bytes": int(df.memory_usage(index=True, deep=True).sum()),
    }


def profile_columns(df: pd.DataFrame) -> list[dict]:
    profiles = []
    for column in df.columns:
        series = df[column]
        entry = {
            "column": str(column),
            "dtype": str(series.dtype),
            "rows": int(len(series)),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": float(series.isna().mean() * 100) if len(series) else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            numeric = series.dropna()
            entry["statistics"] = {
                "min": _json_scalar(numeric.min()) if not numeric.empty else None,
                "max": _json_scalar(numeric.max()) if not numeric.empty else None,
                "mean": _json_scalar(numeric.mean()) if not numeric.empty else None,
                "std": _json_scalar(numeric.std()) if not numeric.empty else None,
            }
        profiles.append(entry)
    return profiles


def _json_scalar(value):
    """Convert numpy scalars to built-in values and non-finite floats to null."""
    if pd.isna(value):
        return None
    return value.item() if hasattr(value, "item") else value
