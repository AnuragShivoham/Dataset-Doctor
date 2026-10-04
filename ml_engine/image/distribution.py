"""Class distribution inferred from immediate parent folder names."""

from collections import Counter
from pathlib import Path

from ..core.result import Finding


def analyze_distribution(records: list[dict], root: str | Path) -> tuple[dict, list[Finding]]:
    root = Path(root)
    counts = Counter()
    for record in records:
        if not record.get("readable"):
            continue
        path = Path(record["path"])
        relative = path.relative_to(root) if root.is_dir() else Path(path.name)
        label = relative.parts[0] if len(relative.parts) > 1 else "unlabeled"
        counts[label] += 1
    classes = dict(sorted(counts.items()))
    findings = []
    if len(counts) >= 2:
        low, high = min(counts.values()), max(counts.values())
        ratio = high / low if low else None
        minorities = [label for label, count in counts.items() if count == low]
        majorities = [label for label, count in counts.items() if count == high]
        severity = "high" if ratio is not None and ratio >= 10 else "medium"
        summary = {"classes": classes,
                   "minority_class": minorities[0] if len(minorities) == 1 else None,
                   "majority_class": majorities[0] if len(majorities) == 1 else None,
                   "imbalance_ratio": round(ratio, 4) if ratio is not None else None,
                   "status": "imbalanced" if ratio is not None and ratio >= 3 else "healthy"}
        if ratio is not None and ratio >= 3:
            findings.append(Finding("image_distribution", "class_imbalance", severity,
                                    f"Image classes have a majority-to-minority count ratio of {ratio:.2f}:1.",
                                    min(10.0, ratio), metadata=summary))
    else:
        summary = {"classes": classes, "minority_class": None, "majority_class": None,
                   "imbalance_ratio": None, "status": "not_assessed" if not counts else "single_class"}
    return summary, findings
