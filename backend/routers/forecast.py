from __future__ import annotations
from fastapi import APIRouter, Query
import backend.data_service as ds
from src.forecasting import prepare_forecasting_series, fit_and_evaluate_forecasting

router = APIRouter()

@router.get("")
def get_forecast(horizon: int = Query(30, ge=7, le=180)):
    df = ds.get_df()
    series = prepare_forecasting_series(df, freq="D")
    if len(series) < 14:
        return {"status": "error", "message": "Insufficient data", "historical": [], "forecast": [], "metrics": {}}

    res = fit_and_evaluate_forecasting(series, horizon=horizon, freq="D")
    if res.get("status") == "error":
        return {"status": "error", "message": res.get("message"), "historical": [], "forecast": [], "metrics": {}}

    hist_data = [
        {"ds": str(dt.date() if hasattr(dt, "date") else dt), "y": round(float(val), 2)}
        for dt, val in series.items()
    ]
    
    fut_df = res["future_df"]
    fut_data = [
        {
            "ds": str(row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]),
            "yhat": round(float(row["Forecast"]), 2),
            "yhat_lower": round(float(row["Lower_95"]), 2),
            "yhat_upper": round(float(row["Upper_95"]), 2),
        }
        for _, row in fut_df.iterrows()
    ]

    metrics = res.get("metrics_model", {})

    return {
        "status": "success",
        "historical": hist_data,
        "forecast": fut_data,
        "metrics": metrics,
    }
