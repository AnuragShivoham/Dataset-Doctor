"""Exact byte-level image duplicate detection."""

import hashlib
from collections import defaultdict

from ..core.result import Finding


def analyze_duplicates(records: list[dict]) -> tuple[dict, list[Finding]]:
    by_hash = defaultdict(list)
    for record in records:
        if record.get("readable"):
            with open(record["path"], "rb") as image_file:
                by_hash[hashlib.sha256(image_file.read()).hexdigest()].append(record["path"])
    groups = [files for files in by_hash.values() if len(files) > 1]
    findings = [Finding("image_duplicates", "duplicate_image", "medium",
                        f"{len(files)} files are byte-identical.", 2.0,
                        metadata={"duplicate_group": index, "files": files, "method": "sha256",
                                  "duplicate_percentage": round(len(files) / len(records) * 100, 2) if records else 0.0})
                for index, files in enumerate(groups, start=1)]
    return {"duplicate_groups": len(groups), "duplicate_files": sum(len(files) for files in groups),
            "method": "sha256"}, findings
