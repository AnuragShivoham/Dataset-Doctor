"""Conservative detection of numeric/date values stored as text."""

import pandas as pd

from ..core.result import Finding


def analyze_datatypes(df: pd.DataFrame) -> tuple[dict, list[Finding], list[str]]:
    columns = []
    findings = []
    recommendations = []
    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        if non_null.empty or not (pd.api.types.is_object_dtype(series.dtype) or
                                  pd.api.types.is_string_dtype(series.dtype)):
            continue
        text = non_null.astype("string").str.strip()
        numeric = pd.to_numeric(text, errors="coerce")
        numeric_ratio = float(numeric.notna().mean())
        parsed_dates = pd.to_datetime(text, errors="coerce", format="mixed")
        date_ratio = float(parsed_dates.notna().mean())
        # Treat a mostly parseable text column with a few exceptions as inconsistent.
        inferred = "numeric" if numeric_ratio >= date_ratio else "datetime"
        ratio = max(numeric_ratio, date_ratio)
        invalid_count = int(len(non_null) - (numeric.notna().sum() if inferred == "numeric" else parsed_dates.notna().sum()))
        columns.append({"column": str(column), "inferred_type": inferred,
                        "parseable_percentage": round(ratio * 100, 2), "inconsistent_count": invalid_count})
        if ratio >= 0.7 and invalid_count:
            examples = text[(numeric.isna() if inferred == "numeric" else parsed_dates.isna())].head(3).tolist()
            findings.append(Finding(
                analyzer="datatypes", issue_type="type_inconsistency", severity="medium",
                message=f"Column contains values inconsistent with an inferred {inferred} type.",
                score_impact=min(5.0, invalid_count / len(non_null) * 10), column=str(column),
                metadata={"inferred_type": inferred, "inconsistent_count": invalid_count,
                          "examples": [str(value) for value in examples]},
            ))
            recommendations.append(f"Review the non-{inferred} values in {column} and confirm the intended data type.")
    return {"columns_checked": columns}, findings, recommendations
