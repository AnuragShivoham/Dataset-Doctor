"""Image file integrity findings."""

from ..core.result import Finding


def analyze_integrity(records: list[dict], unsupported_files: list[str] | None = None) -> tuple[dict, list[Finding]]:
    findings = []
    counts = {"corrupt_images": 0, "zero_byte_files": 0, "unsupported_files": len(unsupported_files or []),
              "invalid_dimensions": 0}
    for record in records:
        error = record.get("error")
        if not error:
            continue
        issue, severity, message = {
            "zero_byte": ("zero_byte_file", "high", "Image file is empty (zero bytes)."),
            "invalid_dimensions": ("invalid_dimensions", "high", "Image has invalid dimensions."),
            "decode_error": ("corrupt_image", "high", "Image could not be decoded; it may be corrupt or truncated."),
        }.get(error, ("corrupt_image", "high", "Image could not be decoded."))
        if issue == "zero_byte_file":
            counts["zero_byte_files"] += 1
        elif issue == "invalid_dimensions":
            counts["invalid_dimensions"] += 1
        else:
            counts["corrupt_images"] += 1
        findings.append(Finding("image_integrity", issue, severity, message, 5.0,
                                column=None, metadata={"file": record["path"], "filename": record["filename"],
                                                       "error_detail": record.get("error_detail")}))
    for path in unsupported_files or []:
        findings.append(Finding("image_integrity", "unsupported_image_format", "medium",
                                "File extension is not among the supported image formats.", 2.0,
                                metadata={"file": path}))
    return counts, findings
