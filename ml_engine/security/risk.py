"""Configurable security finding triage; levels are not probabilities."""

from collections.abc import Mapping, Sequence
from typing import Any

from ..core.result import Finding


def assess_risk(
    findings: Sequence[Finding | Mapping[str, Any]],
    *,
    medium_finding_threshold: int = 3,
    high_finding_threshold: int = 6,
) -> dict[str, Any]:
    """Summarize findings as low/medium/high review priority, not a probability."""
    if medium_finding_threshold < 1:
        raise ValueError("medium_finding_threshold must be at least 1")
    if high_finding_threshold <= medium_finding_threshold:
        raise ValueError("high_finding_threshold must exceed medium_finding_threshold")
    items = [_as_dict(item) for item in findings]
    high_count = sum(str(item.get("severity", "")).lower() in {"high", "critical"} for item in items)
    critical_count = sum(str(item.get("severity", "")).lower() == "critical" for item in items)
    if critical_count or len(items) >= high_finding_threshold:
        level = "high"
    elif high_count or len(items) >= medium_finding_threshold:
        level = "medium"
    else:
        level = "low"
    reasons = []
    for item in items:
        issue = str(item.get("issue_type", "security_finding")).replace("_", " ").capitalize()
        if issue not in reasons:
            reasons.append(issue)
    return {"risk_level": level, "finding_count": len(items),
            "high_severity_count": high_count, "critical_severity_count": critical_count,
            "reasons": reasons,
            "interpretation": "Triage category based on configured finding counts and severities; not a validated probability."}


def _as_dict(finding: Finding | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(finding, Finding):
        return {"issue_type": finding.issue_type, "severity": finding.severity}
    return dict(finding)
