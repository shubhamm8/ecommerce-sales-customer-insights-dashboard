from __future__ import annotations
import platform, sys
from fastapi import APIRouter
import backend.data_service as ds

router = APIRouter()

@router.get("/health")
def get_health():
    df = ds.get_df()
    raw = ds.get_raw_df()
    summary = ds.get_cleaning_summary()
    total = len(df)
    completeness = {}
    for col in df.columns:
        pct = round(df[col].notna().sum() / total * 100, 1) if total > 0 else 0
        completeness[col] = pct
    return {
        "status": "ok",
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "dataset": {
            "clean_rows": len(df),
            "raw_rows": len(raw),
            "columns": list(df.columns),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "date_range": {
                "min": str(df["InvoiceDate"].min().date()) if "InvoiceDate" in df.columns else None,
                "max": str(df["InvoiceDate"].max().date()) if "InvoiceDate" in df.columns else None,
            },
            "completeness": completeness,
        },
        "cleaning_summary": summary,
    }

@router.post("/reload")
def reload_data(num_records: int = 2500, random_seed: int = 42):
    result = ds.reload(num_records=num_records, random_seed=random_seed)
    return {"status": "reloaded", **result}
