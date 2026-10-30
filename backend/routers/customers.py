from __future__ import annotations
from fastapi import APIRouter
import backend.data_service as ds
from src.customer_analysis import compute_customer_summary, analyze_pareto_concentration

router = APIRouter()

@router.get("")
def get_customers(top_n: int = 20):
    df = ds.get_df()
    cust_summary = compute_customer_summary(df)
    pareto = analyze_pareto_concentration(cust_summary)
    
    top_cust = cust_summary.head(top_n).copy()
    if not top_cust.empty:
        top_cust["TotalRevenue"] = top_cust["TotalSpend"]
        if "FirstPurchase" in top_cust.columns:
            top_cust["FirstPurchase"] = top_cust["FirstPurchase"].astype(str)
        if "LastPurchase" in top_cust.columns:
            top_cust["LastPurchase"] = top_cust["LastPurchase"].astype(str)
    
    avg_ltv = float(cust_summary["TotalSpend"].mean()) if not cust_summary.empty else 0.0
    
    return {
        "top_customers": top_cust.to_dict(orient="records"),
        "summary": {
            "unique_customers": len(cust_summary),
            "repeat_customer_rate": round(float((cust_summary["OrderCount"] > 1).sum() / len(cust_summary) * 100), 2) if len(cust_summary) > 0 else 0.0,
            "avg_ltv": round(avg_ltv, 2),
            "pareto_80_pct": pareto.get("top_20_pct_revenue_share", 0.0),
        },
        "pareto": pareto,
    }
