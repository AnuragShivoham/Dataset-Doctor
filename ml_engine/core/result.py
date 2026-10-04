"""Stable serializable result types shared with the API layer."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Finding:
    analyzer: str
    issue_type: str
    severity: str
    message: str
    score_impact: float = 0.0
    column: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    analyzer: str
    status: str
    summary: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
