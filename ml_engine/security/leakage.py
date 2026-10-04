"""Cross-modality potential leakage indicators with supporting evidence."""

from collections.abc import Mapping, Sequence
import re
from typing import Any
from ..core.result import Finding

_IDENTIFIER = re.compile(r"(^|_)(id|uuid|guid|key|index)($|_)", re.IGNORECASE)
_TARGET_DERIVED = re.compile(r"(^|_)(target|label|class|outcome|diagnosis|result)($|_)", re.IGNORECASE)


def analyze_leakage(
    records: Sequence[Mapping[str, Any]],
    *,
    target: str | None = None,
    modality: str = "auto",
    text_column: str = "text",
    label_column: str = "label",
    filename_column: str = "filename",
) -> tuple[dict[str, Any], list[Finding]]:
    """Inspect tabular fields, text content, and image filenames for leakage hints.

    The function reports indicators for human review; it cannot determine
    whether a feature is available at prediction time or task-appropriate.
    """
    if modality not in {"auto", "tabular", "text", "image"}:
        raise ValueError("modality must be auto, tabular, text, or image")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise TypeError("records must be a sequence of mappings")
    if any(not isinstance(record, Mapping) for record in records):
        raise TypeError("each record must be a mapping")

    findings: list[Finding] = []
    evidence_count = 0
    effective_modality = modality
    if modality == "auto":
        keys = {str(key).lower() for record in records for key in record}
        effective_modality = "text" if text_column.lower() in keys else "image" if filename_column.lower() in keys else "tabular"

    if effective_modality == "tabular":
        findings.extend(_tabular_findings(records, target))
    elif effective_modality == "text":
        findings.extend(_text_findings(records, target, text_column, label_column))
    elif effective_modality == "image":
        findings.extend(_image_findings(records, target, label_column, filename_column))
    evidence_count = len(findings)
    return {"modality": effective_modality, "target": target,
            "potential_leakage_count": evidence_count,
            "status": "indicators_found" if evidence_count else "no_indicators_found"}, findings


def _tabular_findings(records: Sequence[Mapping[str, Any]], target: str | None) -> list[Finding]:
    if not records:
        return []
    columns = sorted({str(key) for row in records for key in row})
    findings: list[Finding] = []
    for column in columns:
        if column == target:
            continue
        if _IDENTIFIER.search(column):
            findings.append(Finding("security_leakage", "potential_leakage", "medium",
                                    f"Column {column!r} has an identifier-like name and may expose record identity.", 2.0,
                                    column=column, metadata={"indicator": "identifier_like_column", "target": target}))
        if _TARGET_DERIVED.search(column):
            findings.append(Finding("security_leakage", "potential_leakage", "high",
                                    f"Column {column!r} has a target-like name and may contain target-derived information.", 4.0,
                                    column=column, metadata={"indicator": "target_like_column", "target": target}))
        values = [row.get(column) for row in records if row.get(column) not in (None, "")]
        ratio = len(set(map(str, values))) / len(records) if records else 0.0
        if len(records) >= 20 and ratio >= 0.98:
            findings.append(Finding("security_leakage", "potential_leakage", "medium",
                                    f"Column {column!r} is nearly unique and may identify individual records.", 2.0,
                                    column=column, metadata={"indicator": "near_unique_feature", "unique_ratio": round(ratio, 4), "target": target}))
    if target and target in columns:
        for column in columns:
            if column == target:
                continue
            overlap = [row for row in records if row.get(column) not in (None, "") and row.get(target) not in (None, "")]
            if len(overlap) < 3:
                continue
            matches = [row for row in overlap if str(row[column]).casefold() == str(row[target]).casefold()]
            if overlap and len(matches) / len(overlap) >= 0.98:
                findings.append(Finding("security_leakage", "potential_leakage", "high",
                                        f"Column {column!r} almost exactly matches target {target!r}.", 5.0,
                                        column=column, metadata={"indicator": "target_value_copy", "matching_rows": len(matches),
                                                                 "compared_rows": len(overlap), "target": target}))
                continue
            association = _target_association(overlap, column, target)
            if association is not None and association[1] >= 0.98:
                findings.append(Finding("security_leakage", "potential_leakage", "high",
                                        f"Column {column!r} has a very strong association with target {target!r}; review for target-derived information.", 4.0,
                                        column=column, metadata={"indicator": "strong_target_association",
                                                                 "metric": association[0], "value": round(association[1], 4),
                                                                 "compared_rows": len(overlap), "target": target}))
    return findings


def _target_association(rows: list[Mapping[str, Any]], feature: str, target: str) -> tuple[str, float] | None:
    feature_numbers = [_finite_number(row[feature]) for row in rows]
    target_numbers = [_finite_number(row[target]) for row in rows]
    if all(value is not None for value in feature_numbers + target_numbers):
        x = [float(value) for value in feature_numbers]
        y = [float(value) for value in target_numbers]
        mean_x, mean_y = sum(x) / len(x), sum(y) / len(y)
        covariance = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
        denominator = (sum((a - mean_x) ** 2 for a in x) * sum((b - mean_y) ** 2 for b in y)) ** 0.5
        return ("absolute_pearson_correlation", abs(covariance / denominator)) if denominator else None
    groups: dict[str, set[str]] = {}
    for row in rows:
        groups.setdefault(str(row[feature]), set()).add(str(row[target]))
    if len(groups) < 2:
        return None
    single_target_fraction = sum(len(labels) == 1 for labels in groups.values()) / len(groups)
    return "single_class_group_fraction", single_target_fraction


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number and number not in (float("inf"), float("-inf")) else None


def _text_findings(records: Sequence[Mapping[str, Any]], target: str | None,
                   text_column: str, label_column: str) -> list[Finding]:
    if not target:
        return []
    findings = []
    target_values: list[tuple[str, str]] = []
    for record in records:
        label = record.get(target, record.get(label_column))
        text = record.get(text_column)
        if label not in (None, "") and text not in (None, ""):
            target_values.append((str(label), str(text)))
    matching = [(label, text) for label, text in target_values
                if re.search(rf"(?<!\w){re.escape(label)}(?!\w)", text, re.IGNORECASE)]
    if target_values and len(matching) / len(target_values) >= 0.5:
        labels = sorted({label for label, _ in matching})
        findings.append(Finding("security_leakage", "potential_leakage", "medium",
                                "Text contains its associated label in a substantial share of labeled records; review whether this is expected for the task.",
                                3.0, column=text_column,
                                metadata={"indicator": "label_mentioned_in_text", "matching_records": len(matching),
                                          "labeled_records": len(target_values), "labels": labels[:20], "target": target}))
    metadata_hits = []
    for index, record in enumerate(records):
        for key, value in record.items():
            if str(key) in {text_column, label_column, "id", "record_id"}:
                continue
            if str(key).casefold() == target.casefold() or str(value).casefold() in {label.casefold() for label, _ in target_values}:
                metadata_hits.append({"record": _record_id(record, index), "field": str(key)})
    if metadata_hits:
        findings.append(Finding("security_leakage", "potential_leakage", "medium",
                                "Non-text metadata contains target or label-like values; review whether it will be available at prediction time.",
                                2.0, metadata={"indicator": "target_in_metadata", "matches": metadata_hits[:50], "target": target}))
    return findings


def _image_findings(records: Sequence[Mapping[str, Any]], target: str | None,
                    label_column: str, filename_column: str) -> list[Finding]:
    findings = []
    if not target:
        return findings
    label_values = {str(record.get(label_column)).casefold() for record in records
                    if record.get(label_column) not in (None, "")}
    matches = []
    for index, record in enumerate(records):
        label = record.get(target, record.get(label_column))
        filename = record.get(filename_column, record.get("path", record.get("filename")))
        if label not in (None, "") and filename not in (None, ""):
            label_text = str(label)
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(label_text)}(?![A-Za-z0-9])", str(filename), re.IGNORECASE):
                matches.append({"record": _record_id(record, index), "label": label_text})
        for key, value in record.items():
            if key not in {label_column, target, filename_column, "path", "filename"} and str(value).casefold() in label_values:
                findings.append(Finding("security_leakage", "potential_leakage", "medium",
                                        f"Image metadata field {str(key)!r} contains a class label value.", 2.0,
                                        metadata={"indicator": "label_in_metadata", "record": _record_id(record, index),
                                                  "field": str(key), "target": target}))
    if matches:
        findings.append(Finding("security_leakage", "potential_leakage", "medium",
                                "Image filenames contain their associated class label; review whether filenames are available during prediction.",
                                2.0, column=filename_column,
                                metadata={"indicator": "label_in_filename", "matches": matches[:50], "target": target}))
    return findings


def _record_id(record: Mapping[str, Any], index: int) -> str:
    return str(record.get("id", record.get("record_id", record.get("filename", index))))
