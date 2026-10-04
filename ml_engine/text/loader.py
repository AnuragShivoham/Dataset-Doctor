"""Load TXT folders, CSV, JSON arrays/records, and JSONL into text records."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".txt", ".csv", ".json", ".jsonl"}


@dataclass(frozen=True)
class TextRecord:
    """Normalized in-memory representation of one text document."""

    record_id: str
    text: str
    label: str | None = None
    metadata: dict[str, Any] | None = None


class TextDatasetError(ValueError):
    """Raised when a text dataset cannot be read or normalized."""


def load_text_dataset(
    source: str | Path,
    *,
    text_column: str = "text",
    id_column: str = "id",
    label_column: str = "label",
    as_records: bool = False,
) -> list[dict[str, str | None]] | list[TextRecord]:
    """Load records from TXT, CSV, JSON, JSONL, or a directory of TXT files.

    The default dict shape preserves compatibility with the existing text
    analyzers. Set ``as_records=True`` to receive immutable ``TextRecord``
    instances with source metadata.
    """
    path = Path(source)
    if not path.exists():
        raise TextDatasetError(f"Text dataset not found: {path}")
    if path.is_dir():
        files = sorted(item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS)
        records = []
        for file_path in files:
            relative = file_path.relative_to(path)
            inferred_label = relative.parts[0] if len(relative.parts) > 1 else None
            file_records = _load_file(file_path, text_column, id_column, label_column)
            for index, record in enumerate(file_records):
                record["id"] = f"{relative.as_posix()}#{record['id']}" if file_path.suffix.lower() != ".txt" else relative.as_posix()
                if not record.get("label"):
                    record["label"] = inferred_label
                record["_metadata"] = {"source": str(file_path), "index": index, "relative_path": relative.as_posix()}
            records.extend(file_records)
        if not records:
            raise TextDatasetError(f"No supported text files found in: {path}")
        return _convert_records(records) if as_records else _public_records(records)
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise TextDatasetError(f"Unsupported text dataset format: {extension or '(no extension)'}")
    if extension == ".txt":
        records = [{"id": path.name, "text": _read_text(path), "label": None,
                    "_metadata": {"source": str(path), "extension": extension}}]
        return _convert_records(records) if as_records else _public_records(records)
    records = _load_file(path, text_column, id_column, label_column)
    for index, record in enumerate(records):
        record["_metadata"] = {"source": str(path), "row": index, "extension": extension}
    return _convert_records(records) if as_records else _public_records(records)


def _load_file(path: Path, text_column: str, id_column: str, label_column: str) -> list[dict[str, Any]]:
    extension = path.suffix.lower()
    if extension == ".txt":
        return [{"id": path.name, "text": _read_text(path), "label": None}]
    if extension == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as source_file:
            reader = csv.DictReader(source_file)
            if not reader.fieldnames or text_column not in reader.fieldnames:
                raise TextDatasetError(f"CSV must contain the text column {text_column!r}: {path}")
            return [_record(row, index, id_column, text_column, label_column)
                    for index, row in enumerate(reader, start=1)]
    if extension == ".jsonl":
        records = []
        for index, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TextDatasetError(f"Invalid JSONL row {index}: {path}") from exc
            if not isinstance(value, dict):
                raise TextDatasetError(f"JSONL row {index} must be an object: {path}")
            records.append(_record(value, index, id_column, text_column, label_column))
        return records
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise TextDatasetError(f"Invalid JSON file: {path}") from exc
    if isinstance(value, dict):
        value = value.get("records", value.get("data", [value]))
    if not isinstance(value, list):
        raise TextDatasetError("JSON dataset must be an array of objects or an object containing records/data")
    if not all(isinstance(row, dict) for row in value):
        raise TextDatasetError("JSON dataset rows must be objects")
    return [_record(row, index, id_column, text_column, label_column)
            for index, row in enumerate(value, start=1)]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TextDatasetError(f"Text file is not valid UTF-8: {path}") from exc


def _record(row: dict[str, Any], index: int, id_column: str, text_column: str, label_column: str) -> dict[str, str | None]:
    if text_column not in row:
        raise TextDatasetError(f"Record {index} does not contain the text field {text_column!r}")
    record_id = row.get(id_column)
    label = row.get(label_column)
    text = row.get(text_column)
    return {"id": str(record_id) if record_id is not None else str(index),
            "text": "" if text is None else str(text),
            "label": str(label) if label is not None else None}


def _convert_records(records: list[dict[str, Any]]) -> list[TextRecord]:
    return [TextRecord(record_id=str(record["id"]), text=str(record["text"]),
                       label=record.get("label"), metadata=record.get("_metadata"))
            for record in records]


def _public_records(records: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    """Keep the established analyzer-facing record shape stable."""
    return [{"id": str(record["id"]), "text": str(record["text"]), "label": record.get("label")}
            for record in records]
