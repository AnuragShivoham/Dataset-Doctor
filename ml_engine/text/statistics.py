"""Document and corpus-level text length statistics."""

import re
import statistics as std_statistics


WORD_PATTERN = re.compile(r"\b\w+\b", flags=re.UNICODE)


def analyze_statistics(records: list[dict], min_words: int = 3, max_words: int = 1000) -> dict:
    if min_words < 0 or max_words < min_words:
        raise ValueError("Require 0 <= min_words <= max_words")
    word_counts = [len(WORD_PATTERN.findall(record.get("text", ""))) for record in records]
    char_counts = [len(record.get("text", "")) for record in records]
    empty = sum(not record.get("text", "").strip() for record in records)
    labels = [record.get("label") for record in records if record.get("label") not in (None, "")]
    from collections import Counter
    label_counts = dict(sorted(Counter(labels).items()))
    return {
        "document_count": len(records),
        "total_characters": sum(char_counts),
        "total_words": sum(word_counts),
        "average_characters": round(sum(char_counts) / len(records), 2) if records else 0.0,
        "average_words": round(sum(word_counts) / len(records), 2) if records else 0.0,
        "minimum_words": min(word_counts, default=0),
        "maximum_words": max(word_counts, default=0),
        "median_words": float(std_statistics.median(word_counts)) if word_counts else 0.0,
        "empty_documents": empty,
        "very_short_documents": sum(0 < count < min_words for count in word_counts),
        "very_long_documents": sum(count > max_words for count in word_counts),
        "min_words_threshold": min_words,
        "max_words_threshold": max_words,
        "label_distribution": label_counts,
        "unlabeled_documents": len(records) - len(labels),
    }
