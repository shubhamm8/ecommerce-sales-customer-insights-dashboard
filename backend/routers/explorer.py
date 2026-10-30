from __future__ import annotations
from fastapi import APIRouter, Query
import backend.data_service as ds
import pandas as pd

router = APIRouter()

@router.get("")
def get_explorer_data(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str = Query("", description="Search text"),
):
    df = ds.get_df()
    if df.empty:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    filtered = df
    if search.strip():
        s = search.strip().lower()
        masks = []
        for col in ["InvoiceNo", "StockCode", "Description", "CustomerID", "Country"]:
            if col in df.columns:
                masks.append(df[col].astype(str).str.lower().str.contains(s, na=False))
        if masks:
            combined_mask = masks[0]
            for m in masks[1:]:
                combined_mask |= m
            filtered = df[combined_mask]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = filtered.iloc[start:end].copy()

    for col in sliced.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        sliced[col] = sliced[col].astype(str)

    # Convert NaNs to None for valid JSON serialization
    records = sliced.fillna("").to_dict(orient="records")

    return {
        "items": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
    }
