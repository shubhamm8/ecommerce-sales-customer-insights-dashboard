from __future__ import annotations
from fastapi import APIRouter
import backend.data_service as ds
from src.metrics import compute_executive_kpis, compute_period_over_period

router = APIRouter()

@router.get("")
def get_kpis():
    df = ds.get_df()
    kpis = compute_executive_kpis(df)
    pop  = compute_period_over_period(df)
    return {"kpis": kpis, "period_over_period": pop}
