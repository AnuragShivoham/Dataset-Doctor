"""Dataset-agnostic statistical anomaly indicators with reviewable evidence.

These are data-quality signals only. They do not establish malicious activity.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
import math
import re
import statistics
from typing import Any

from ..core.result import Finding

_IDENTIFIER_NAME = re.compile(r"(^|_)(id|uuid|guid|key|index)($|_)", re.IGNORECASE)


def analyze_anomalies(
    records: Sequence[Mapping[str, Any]],
    *,
    numeric_z_threshold: float = 4.0,
    rare_category_fraction: float = 0.01,
    missingness_threshold: float = 0.50,
    max_categories: int = 20,
) -> tuple[dict[str, Any], list[Finding]]:
    """Flag extreme numeric values, rare low-cardinality values, and missingness.

    Each finding includes counts or record identifiers as evidence. Identifier-
    named and high-cardinality columns are excluded from rare-category checks.
    Input records are never modified.
    """
    if numeric_z_threshold <= 0:
        raise ValueError("numeric_z_threshold must be greater than zero")
    if not 0 < rare_category_fraction <= 1:
        raise ValueError("rare_category_fraction must be in (0, 1]")
    if not 0 < missingness_threshold <= 1:
        raise ValueError("missingness_threshold must be in (0, 1]")
    if max_categories < 2:
        raise ValueError("max_categories must be at least 2")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise TypeError("records must be a sequence of mappings")
    if any(not isinstance(record, Mapping) for record in records):
        raise TypeError("each record must be a mapping")

    count = len(records)
    columns = sorted({str(key) for record in records for key in record})
    summary: dict[str, Any] = {
        "record_count": count,
        "numeric_anomaly_count": 0,
        "rare_category_count": 0,
        "missingness_anomaly_count": 0,
        "columns_checked": columns,
    }
    findings: list[Finding] = []
    if not count:
        summary["finding_count"] = 0
        return summary, findings

    for column in columns:
        values = [record.get(column) for record in records]
        present = [value for value in values if not _is_missing(value)]
        missing = count - len(present)
        missing_fraction = missing / count
        if missing and count >= 2 and missing_fraction >= missingness_threshold:
            summary["missingness_anomaly_count"] += 1
            findings.append(Finding(
                "security_anomaly", "unusual_missingness", "medium",
                f"Column {column!r} is missing in {missing} of {count} records.",
                2.0, column=column,
                metadata={"missing_count": missing, "record_count": count,
                          "missing_fraction": round(missing_fraction, 4),
                          "records": [_record_id(record, index) for index, record in enumerate(records)
                                      if _is_missing(record.get(column))]},
            ))

        numeric_values = [(index, _finite_number(value)) for index, value in enumerate(values)]
        numeric_values = [(index, value) for index, value in numeric_values if value is not None]
        if len(numeric_values) >= 4 and len(numeric_values) / max(1, len(present)) >= 0.8:
            outliers, method, limit = _numeric_outliers(numeric_values, numeric_z_threshold)
            if outliers:
                summary["numeric_anomaly_count"] += len(outliers)
                findings.append(Finding(
                    "security_anomaly", "extreme_numeric_value", "medium",
                    f"Column {column!r} contains {len(outliers)} statistically extreme numeric value(s).",
                    min(10.0, len(outliers) * 1.0), column=column,
                    metadata={"method": method, "threshold": limit,
                              "records": [{"id": _record_id(records[index], index), "value": value}
                                          for index, value in outliers]},
                ))
            continue

        if _IDENTIFIER_NAME.search(column) or len(present) < 2:
            continue
        try:
            distinct = set(present)
        except TypeError:
            continue
        if len(distinct) < 2 or len(distinct) > min(max_categories, max(2, int(math.sqrt(count)) + 1)):
            continue
        categories = Counter(str(value) for value in present)
        rare = [(category, frequency) for category, frequency in categories.items()
                if frequency / count <= rare_category_fraction]
        for category, frequency in sorted(rare):
            summary["rare_category_count"] += 1
            matching = [_record_id(record, index) for index, record in enumerate(records)
                        if not _is_missing(record.get(column)) and str(record.get(column)) == category]
            findings.append(Finding(
                "security_anomaly", "rare_category", "low",
                f"Column {column!r} contains a rare category observed {frequency} time(s).",
                1.0, column=column,
                metadata={"category": category, "count": frequency,
                          "record_count": count, "fraction": round(frequency / count, 4),
                          "records": matching},
            ))

    summary["finding_count"] = len(findings)
    return summary, findings


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and not value.strip()


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _numeric_outliers(values: list[tuple[int, float]], threshold: float) -> tuple[list[tuple[int, float]], str, float]:
    numbers = [value for _, value in values]
    median = statistics.median(numbers)
    deviations = [abs(value - median) for value in numbers]
    mad = statistics.median(deviations)
    if mad > 0:
        outliers = [(index, value) for index, value in values
                    if abs(0.6745 * (value - median) / mad) > threshold]
        return outliers, "modified_z_score", threshold
    q1, q3 = _quantile(numbers, 0.25), _quantile(numbers, 0.75)
    iqr = q3 - q1
    if iqr <= 0:
        return [], "iqr", 1.5
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [(index, value) for index, value in values if value < lower or value > upper], "iqr", 1.5


def _quantile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _record_id(record: Mapping[str, Any], index: int) -> str:
    return str(record.get("id", record.get("record_id", index)))
