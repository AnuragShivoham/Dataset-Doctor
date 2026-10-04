"""Aggregate independent data signals into cautious review indicators."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from ..core.result import Finding

_SIGNAL_TYPES = {
    "extreme_numeric_value", "rare_category", "unusual_missingness",
    "potential_leakage", "possible_label_inconsistency", "duplicate_text",
    "duplicate_image", "semantic_outlier", "possible_pii",
}


def aggregate_poisoning_indicators(
    findings: Sequence[Finding | Mapping[str, Any]],
    *,
    min_independent_signals: int = 2,
) -> tuple[dict[str, Any], list[Finding]]:
    """Flag records supported by multiple signal types; never diagnose poisoning.

    Signals with record identifiers are grouped per record. Dataset-level
    signals without record identifiers can still be aggregated only when they
    are distinct issue types. The result is explicitly an investigation cue.
    """
    if min_independent_signals < 2:
        raise ValueError("min_independent_signals must be at least 2")
    per_record: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    dataset_signals: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for finding in findings:
        item = _as_dict(finding)
        issue = str(item.get("issue_type", ""))
        if issue not in _SIGNAL_TYPES:
            continue
        metadata = item.get("metadata") or {}
        records = _record_ids(metadata)
        evidence = {"issue_type": issue, "severity": str(item.get("severity", "low")),
                    "message": str(item.get("message", issue))}
        if records:
            for record_id in records:
                per_record[record_id][issue].append(evidence)
        else:
            dataset_signals[issue].append(evidence)

    output = []
    for record_id, issue_groups in sorted(per_record.items()):
        if len(issue_groups) < min_independent_signals:
            continue
        evidence = [entry for issue in sorted(issue_groups) for entry in issue_groups[issue]]
        output.append(Finding(
            "security_poisoning", "potential_poisoning_indicator", "high",
            "Multiple independent data-quality signals warrant investigation; this is not a poisoning determination.",
            0.0, metadata={"records": [record_id], "evidence": evidence,
                           "signal_types": sorted(issue_groups)},
        ))
    if len(dataset_signals) >= min_independent_signals:
        evidence = [entry for issue in sorted(dataset_signals) for entry in dataset_signals[issue]]
        output.append(Finding(
            "security_poisoning", "potential_poisoning_indicator", "medium",
            "Multiple dataset-level signals warrant investigation; this is not a poisoning determination.",
            0.0, metadata={"evidence": evidence, "signal_types": sorted(dataset_signals)},
        ))
    return {"input_finding_count": len(findings), "eligible_signal_types": sorted(_SIGNAL_TYPES),
            "potential_indicator_count": len(output),
            "status": "indicators_found" if output else "no_aggregated_indicator"}, output


def _as_dict(finding: Finding | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(finding, Finding):
        return {"issue_type": finding.issue_type, "severity": finding.severity,
                "message": finding.message, "metadata": finding.metadata}
    return dict(finding)


def _record_ids(metadata: Mapping[str, Any]) -> list[str]:
    values = []
    for key in ("record", "document", "id", "record_id"):
        if metadata.get(key) is not None:
            values.append(str(metadata[key]))
    for key in ("records", "documents", "files", "matches"):
        raw = metadata.get(key)
        if isinstance(raw, (list, tuple)):
            for value in raw:
                if isinstance(value, Mapping):
                    candidate = value.get("id", value.get("record", value.get("filename", value.get("path"))))
                    if candidate is not None:
                        values.append(str(candidate))
                else:
                    values.append(str(value))
    return sorted(set(values))
