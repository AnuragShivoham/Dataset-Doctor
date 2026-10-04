"""Configurable text completeness and length quality findings."""

from ..core.result import Finding
from .statistics import WORD_PATTERN


def analyze_quality(records: list[dict], min_words: int = 3, max_words: int = 1000) -> tuple[dict, list[Finding]]:
    if min_words < 0 or max_words < min_words:
        raise ValueError("Require 0 <= min_words <= max_words")
    findings = []
    empty_count = short_count = long_count = 0
    for record in records:
        text = record.get("text", "")
        document_id = str(record.get("id", "unknown"))
        word_count = len(WORD_PATTERN.findall(text))
        if not text.strip():
            empty_count += 1
            findings.append(Finding("text_quality", "empty_text", "high",
                                    "Document contains no non-whitespace text.", 5.0,
                                    metadata={"document": document_id, "word_count": 0}))
        elif word_count < min_words:
            short_count += 1
            findings.append(Finding("text_quality", "possible_short_text", "low",
                                    f"Document has {word_count} words, below the configured minimum of {min_words}.", 1.0,
                                    metadata={"document": document_id, "word_count": word_count,
                                              "minimum_words": min_words}))
        elif word_count > max_words:
            long_count += 1
            findings.append(Finding("text_quality", "very_long_document", "medium",
                                    f"Document has {word_count} words, above the configured maximum of {max_words}.", 2.0,
                                    metadata={"document": document_id, "word_count": word_count,
                                              "maximum_words": max_words}))
    return {"empty_documents": empty_count, "very_short_documents": short_count,
            "very_long_documents": long_count, "min_words_threshold": min_words,
            "max_words_threshold": max_words}, findings
