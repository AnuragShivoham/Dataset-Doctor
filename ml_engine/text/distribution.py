"""Label distribution diagnostics for text classification datasets."""

from collections import Counter

from ..core.result import Finding


def analyze_distribution(records: list[dict], imbalance_threshold: float = 3.0) -> tuple[dict, list[Finding]]:
    labels = [record["label"] for record in records if record.get("label") not in (None, "")]
    counts = Counter(labels)
    total = sum(counts.values())
    classes = {label: {"count": count, "percentage": round(count / total * 100, 2)}
               for label, count in sorted(counts.items())} if total else {}
    findings = []
    if len(counts) >= 2:
        low, high = min(counts.values()), max(counts.values())
        ratio = high / low if low else None
        minorities = [label for label, count in counts.items() if count == low]
        majorities = [label for label, count in counts.items() if count == high]
        summary = {"class_count": len(counts), "classes": classes,
                   "minority_class": minorities[0] if len(minorities) == 1 else None,
                   "majority_class": majorities[0] if len(majorities) == 1 else None,
                   "imbalance_ratio": round(ratio, 4) if ratio is not None else None,
                   "status": "imbalanced" if ratio is not None and ratio >= imbalance_threshold else "healthy"}
        if ratio is not None and ratio >= imbalance_threshold:
            findings.append(Finding("text_distribution", "class_imbalance",
                                    "high" if ratio >= 10 else "medium",
                                    f"Text labels have a majority-to-minority count ratio of {ratio:.2f}:1.",
                                    min(10.0, ratio), metadata={**summary, "imbalance_ratio": ratio}))
    else:
        summary = {"class_count": len(counts), "classes": classes,
                   "minority_class": None, "majority_class": None,
                   "imbalance_ratio": None,
                   "status": "not_assessed" if not counts else "single_class"}
    summary["unlabeled_documents"] = len(records) - len(labels)
    return summary, findings
