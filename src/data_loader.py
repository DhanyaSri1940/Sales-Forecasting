"""Load the original raw CSV. Never mutate the file on disk."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.utils import DATA_RAW, EXPECTED_COLUMNS, RAW_CSV_NAME


def raw_csv_path() -> Path:
    path = DATA_RAW / RAW_CSV_NAME
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {path}. Copy the original CSV into data/raw/."
        )
    return path


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(raw_csv_path())
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if missing:
        raise ValueError(f"Raw dataset is missing expected columns: {missing}")
    if extra:
        raise ValueError(f"Raw dataset contains unexpected columns: {extra}")
    return df
