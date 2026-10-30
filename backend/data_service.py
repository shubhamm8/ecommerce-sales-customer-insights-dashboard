"""
Singleton data service — loads and caches the e-commerce dataset at startup.
Shared across all FastAPI route handlers.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.data_cleaning import clean_ecommerce_data
from src.data_loader import generate_synthetic_ecommerce_data, load_dataset_from_source

_raw_df: pd.DataFrame | None = None
_clean_df: pd.DataFrame | None = None
_cleaning_summary: dict | None = None


def _load() -> None:
    global _raw_df, _clean_df, _cleaning_summary
    sample_path = PROJECT_ROOT / "data" / "sample_ecommerce.csv"
    if sample_path.exists():
        raw = load_dataset_from_source(sample_path)
    else:
        raw = generate_synthetic_ecommerce_data(num_records=2500, random_seed=42)
    cleaned, summary = clean_ecommerce_data(raw)
    _raw_df = raw
    _clean_df = cleaned
    _cleaning_summary = summary


def get_df() -> pd.DataFrame:
    if _clean_df is None:
        _load()
    return _clean_df


def get_raw_df() -> pd.DataFrame:
    if _raw_df is None:
        _load()
    return _raw_df


def get_cleaning_summary() -> dict:
    if _cleaning_summary is None:
        _load()
    return _cleaning_summary


def reload(num_records: int = 2500, random_seed: int = 42) -> dict:
    """Regenerate synthetic data and reload."""
    global _raw_df, _clean_df, _cleaning_summary
    raw = generate_synthetic_ecommerce_data(num_records=num_records, random_seed=random_seed)
    cleaned, summary = clean_ecommerce_data(raw)
    _raw_df = raw
    _clean_df = cleaned
    _cleaning_summary = summary
    return {"rows_clean": len(cleaned), "rows_raw": len(raw)}
