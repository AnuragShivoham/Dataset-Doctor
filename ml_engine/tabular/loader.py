"""Load common tabular files into pandas DataFrames."""

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def load_tabular_dataset(file_path: str | Path) -> pd.DataFrame:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    if not path.is_file():
        raise ValueError(f"Dataset path is not a file: {path}")

    extension = path.suffix.lower()
    if extension == ".csv":
        return pd.read_csv(path)
    if extension in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(
        f"Unsupported file type: {extension or '(no extension)'}. "
        f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
    )
