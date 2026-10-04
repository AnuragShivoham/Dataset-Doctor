"""Deterministic PII pattern indicators; matched sensitive values are never returned."""

import re

from ..core.result import Finding

PATTERNS = {
    "email": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?!\w)", re.IGNORECASE),
    "phone": re.compile(r"(?<!\w)(?:\+?\d[\d().\s-]{7,}\d)(?!\w)"),
    "ip_address": re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"),
    "url": re.compile(r"\b(?:https?://|www\.)[^\s<>]+", re.IGNORECASE),
    "credit_card_like": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
}


def analyze_pii(records: list[dict]) -> tuple[dict, list[Finding]]:
    findings = []
    totals = {name: 0 for name in PATTERNS}
    documents_with_matches = set()
    for record in records:
        text = record.get("text", "")
        document_id = str(record.get("id", "unknown"))
        for pattern_name, regex in PATTERNS.items():
            matches = list(regex.finditer(text))
            if pattern_name == "credit_card_like":
                matches = [match for match in matches if _passes_luhn(match.group())]
            if matches:
                count = len(matches)
                totals[pattern_name] += count
                documents_with_matches.add(document_id)
                findings.append(Finding(
                    "text_privacy", "possible_pii", "high",
                    f"Possible {pattern_name.replace('_', ' ')} indicator detected.", 5.0,
                    metadata={"pattern": pattern_name, "count": count, "document": document_id},
                ))
    return {"pattern_counts": totals, "documents_with_possible_pii": len(documents_with_matches)}, findings


def _passes_luhn(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0
