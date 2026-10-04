"""Exact and whitespace/case-normalized text duplicate diagnostics."""

from collections import defaultdict
import re

from ..core.result import Finding


def normalize_text(text: str) -> str:
    """Normalize case and whitespace while preserving punctuation."""
    return re.sub(r"\s+", " ", text.strip()).casefold()


def analyze_duplicates(records: list[dict]) -> tuple[dict, list[Finding]]:
    normalized_groups = defaultdict(list)
    exact_groups = defaultdict(list)
    for record in records:
        text = record.get("text", "")
        document_id = str(record.get("id", "unknown"))
        exact_groups[text].append(document_id)
        normalized_groups[normalize_text(text)].append((document_id, text))
    findings = []
    duplicate_docs = set()
    exact_group_count = 0
    normalized_group_count = 0
    for documents in exact_groups.values():
        if len(documents) > 1:
            exact_group_count += 1
            duplicate_docs.update(documents[1:])
            findings.append(Finding("text_duplicates", "duplicate_text", "medium",
                                    f"{len(documents)} documents contain exactly identical text.", 2.0,
                                    metadata={"duplicate_type": "exact", "documents": documents,
                                              "duplicate_groups": 1, "duplicate_documents": len(documents) - 1}))
    for documents in normalized_groups.values():
        if len(documents) > 1 and len({text for _, text in documents}) > 1:
            normalized_group_count += 1
            duplicate_docs.update(document_id for document_id, _ in documents[1:])
            findings.append(Finding("text_duplicates", "duplicate_text", "medium",
                                    f"{len(documents)} documents match after whitespace and case normalization.", 2.0,
                                    metadata={"duplicate_type": "normalized",
                                              "documents": [document_id for document_id, _ in documents],
                                              "duplicate_groups": 1,
                                              "duplicate_documents": len(documents) - 1}))
    return {"exact_duplicate_groups": exact_group_count,
            "normalized_duplicate_groups": normalized_group_count,
            "duplicate_groups": exact_group_count + normalized_group_count,
            "duplicate_documents": len(duplicate_docs)}, findings
