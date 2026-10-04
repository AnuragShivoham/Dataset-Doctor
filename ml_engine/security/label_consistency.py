"""Find repeated or near-identical samples carrying conflicting labels."""

from collections.abc import Mapping, Sequence
from difflib import SequenceMatcher
import hashlib
import math
import re
from pathlib import Path
from typing import Any

from ..core.result import Finding


def analyze_label_consistency(
    records: Sequence[Mapping[str, Any]],
    *,
    sample_column: str | None = None,
    label_column: str = "label",
    similarity_threshold: float = 0.95,
    max_records: int = 2000,
) -> tuple[dict[str, Any], list[Finding]]:
    """Flag matching text or byte-identical file samples with different labels.

    Text comparisons use normalized exact equality first, then a character
    similarity ratio. File paths are compared by SHA-256. This deliberately
    does not claim semantic similarity or prove label errors.
    """
    if not 0 < similarity_threshold <= 1:
        raise ValueError("similarity_threshold must be in (0, 1]")
    if max_records < 2:
        raise ValueError("max_records must be at least 2")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise TypeError("records must be a sequence of mappings")
    if any(not isinstance(record, Mapping) for record in records):
        raise TypeError("each record must be a mapping")
    if len(records) > max_records:
        raise ValueError(f"record count exceeds configured pairwise comparison limit ({max_records})")
    column = sample_column or _choose_sample_column(records)
    summary = {"record_count": len(records), "sample_column": column,
               "compared_pairs": 0, "inconsistent_pairs": 0,
               "status": "not_assessed" if column is None else "consistent"}
    if column is None:
        return summary, []

    samples = []
    for index, record in enumerate(records):
        label = record.get(label_column)
        value = record.get(column)
        normalized, method = _sample_key(value, column)
        samples.append((_record_id(record, index), None if label is None else str(label), normalized, method))

    findings = []
    for left in range(len(samples)):
        left_id, left_label, left_value, left_method = samples[left]
        if left_label is None or left_label == "" or left_value is None:
            continue
        for right in range(left + 1, len(samples)):
            right_id, right_label, right_value, right_method = samples[right]
            if right_label is None or right_label == "" or right_value is None:
                continue
            summary["compared_pairs"] += 1
            if left_label == right_label:
                continue
            if left_value == right_value:
                similarity = 1.0
                method = "exact" if left_method == right_method == "text" else "sha256"
            elif left_method == right_method == "text":
                similarity = SequenceMatcher(None, left_value, right_value, autojunk=False).ratio()
                method = "character_similarity"
            else:
                continue
            if similarity >= similarity_threshold:
                summary["inconsistent_pairs"] += 1
                findings.append(Finding(
                    "security_label_consistency", "possible_label_inconsistency", "high",
                    "Highly similar samples have different labels; review the examples and task context.",
                    5.0, metadata={"records": [left_id, right_id], "labels": [left_label, right_label],
                                   "similarity": round(similarity, 4), "method": method,
                                   "reason": "Highly similar samples have different labels."},
                ))
    if findings:
        summary["status"] = "inconsistencies_found"
    return summary, findings


def _choose_sample_column(records: Sequence[Mapping[str, Any]]) -> str | None:
    keys = {str(key) for record in records for key in record}
    for candidate in ("text", "content", "document", "path"):
        if candidate in keys:
            return candidate
    return None


def _sample_key(value: Any, column: str) -> tuple[str | None, str]:
    if value is None:
        return None, "text"
    if column == "path" and isinstance(value, (str, Path)):
        path = Path(value)
        if path.is_file():
            try:
                return hashlib.sha256(path.read_bytes()).hexdigest(), "file"
            except OSError:
                return None, "file"
    text = re.sub(r"\s+", " ", str(value).strip()).casefold()
    return (text if text else None), "text"


def _record_id(record: Mapping[str, Any], index: int) -> str:
    return str(record.get("id", record.get("record_id", record.get("filename", index))))
