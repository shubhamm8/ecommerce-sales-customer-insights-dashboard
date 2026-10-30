from __future__ import annotations
from fastapi import APIRouter
import backend.data_service as ds
from src.forecasting import prepare_forecasting_series
from src.anomaly_detection import run_anomaly_detection

router = APIRouter()

@router.get("")
def get_anomalies():
    df = ds.get_df()
    daily_series = prepare_forecasting_series(df, freq="D")
    if len(daily_series) < 7:
        return {"time_series": [], "anomalies": [], "summary": {}}

    res = run_anomaly_detection(daily_series, method="rolling")
    if res.get("status") == "error":
        return {"time_series": [], "anomalies": [], "summary": {}}

    df_anom = res["df_anomalies"]
    
    ts_data = []
    anom_data = []
    for _, row in df_anom.iterrows():
        dt_str = str(row["Date"].date() if hasattr(row["Date"], "date") else row["Date"])
        val = round(float(row["Value"]), 2)
        item = {"InvoiceDate": dt_str, "NetRevenue": val}
        ts_data.append(item)
        if row["IsAnomaly"]:
            anom_data.append({
                "InvoiceDate": dt_str,
                "NetRevenue": val,
                "anomaly_score": round(float(row.get("Score", 0)), 3),
                "z_score": round(float(row.get("Deviation", 0)), 2),
            })

    avg_anom_rev = sum(a["NetRevenue"] for a in anom_data) / len(anom_data) if anom_data else 0.0

    return {
        "time_series": ts_data,
        "anomalies": anom_data,
        "summary": {
            "anomaly_rate": round(float(res.get("anomaly_rate", 0)), 1),
            "avg_anomaly_revenue": round(avg_anom_rev, 2),
            "method": "Rolling Window (7-Day)",
        },
    }
