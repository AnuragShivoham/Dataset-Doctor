"""Map diagnostic findings to deduplicated, prioritized human actions."""

from collections.abc import Mapping

from ..core.result import Finding

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def generate_recommendations(findings: list[Finding | Mapping]) -> list[dict]:
    recommendations = []
    seen = set()
    for finding in sorted((_as_dict(item) for item in findings),
                          key=lambda item: PRIORITY_ORDER.get(str(item.get("severity", "low")).lower(), 3)):
        issue = finding.get("issue_type", "data_quality")
        column = finding.get("column")
        if issue == "missing_values":
            action = f"Review missing-value handling for {column}."
            category = "missing_values"
        elif issue == "duplicate_rows":
            action = "Review duplicate rows and remove them only if they are accidental repeats."
            category = "duplicates"
        elif issue == "outliers":
            action = f"Investigate extreme values in {column} before deciding whether to transform, cap, remove, or retain them."
            category = "outliers"
        elif issue == "type_inconsistency":
            action = f"Review values in {column} that do not match the inferred data type."
            category = "validity"
        elif issue == "class_imbalance":
            action = "Consider class weighting or resampling during model training; keep the source dataset unchanged."
            category = "balance"
        elif issue == "possible_data_leakage":
            action = f"Review whether {column} should be used as a model feature and whether it is available at prediction time."
            category = "leakage"
        elif issue == "suspicious_target_relationship":
            action = f"Verify that {column} is a legitimate pre-outcome feature and is not derived from the target."
            category = "leakage"
        elif issue in {"corrupt_image", "zero_byte_file", "unsupported_image_format", "invalid_dimensions"}:
            action = f"Review image file {((finding.get('metadata') or {}).get('filename') or (finding.get('metadata') or {}).get('file', 'reported'))} and replace or convert it only if appropriate."
            category = "image_integrity"
        elif issue == "duplicate_image":
            action = "Review byte-identical images and retain duplicates only when repeated examples are intentional."
            category = "image_duplicates"
        elif issue == "semantic_outlier":
            action = "Manually review this image because its visual content may not match the expected dataset or class."
            category = "data_review"
        elif issue == "low_resolution":
            action = "Check whether the image resolution is sufficient for the intended task."
            category = "image_quality"
        elif issue == "possible_blur":
            action = "Review the image for blur; the Laplacian score is a signal and may not match task-specific quality needs."
            category = "image_quality"
        elif issue in {"brightness_anomaly", "extreme_aspect_ratio"}:
            action = "Review the measured image characteristics in context; this signal alone does not mean the image is unsuitable."
            category = "image_quality"
        else:
            action = f"Investigate {finding.get('message', issue)}"
            category = issue
        key = (category, action)
        if key not in seen:
            seen.add(key)
            recommendations.append({"priority": str(finding.get("severity", "low")).lower(),
                                    "category": category, "issue_type": issue,
                                    "column": column, "action": action})
    return recommendations


def _as_dict(item: Finding | Mapping) -> dict:
    if isinstance(item, Finding):
        return {"issue_type": item.issue_type, "severity": item.severity,
                "message": item.message, "column": item.column,
                "metadata": item.metadata}
    return dict(item)
