"""Utility helpers for SCORE repository scripts."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


SCORE_COLUMNS = [
    "Safety",
    "Consensus",
    "Objectivity",
    "Reproducibility",
    "Explainability",
]


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if it does not already exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path



def read_tabular_file(path: str | Path) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)

    raise ValueError(f"Unsupported file type: {suffix}")



def write_tabular_file(df: pd.DataFrame, path: str | Path) -> None:
    """Write a DataFrame to CSV or Excel."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(path, index=False)
        return
    if suffix in {".xlsx", ".xls"}:
        df.to_excel(path, index=False)
        return

    raise ValueError(f"Unsupported output type: {suffix}")



def validate_score_columns(df: pd.DataFrame) -> None:
    """Ensure all expected SCORE dimensions are present."""
    missing = [column for column in SCORE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(
            "Missing SCORE columns: " + ", ".join(missing)
        )
