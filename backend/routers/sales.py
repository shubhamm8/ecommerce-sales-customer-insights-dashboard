from __future__ import annotations
from fastapi import APIRouter, Query
import backend.data_service as ds
from src.sales_analysis import aggregate_sales_time_series, analyze_geographic_sales

router = APIRouter()

@router.get("/timeseries")
def get_timeseries(freq: str = Query("W", description="D | W | M")):
    df = ds.get_df()
    ts = aggregate_sales_time_series(df, freq=freq)
    ts["InvoiceDate"] = ts["Date"].astype(str) if "Date" in ts.columns else ts["InvoiceDate"].astype(str)
    if "Revenue" in ts.columns and "NetRevenue" not in ts.columns:
        ts["NetRevenue"] = ts["Revenue"]
    return ts.to_dict(orient="records")

@router.get("/products")
def get_products(top_n: int = Query(10)):
    df = ds.get_df()
    valid = df[df.get("Quantity", 1) > 0].copy()
    
    rev_col = "NetRevenue" if "NetRevenue" in valid.columns else ("LineTotal" if "LineTotal" in valid.columns else None)
    if rev_col is None:
        valid["ComputedRevenue"] = valid["Quantity"] * valid.get("UnitPrice", 1.0)
        rev_col = "ComputedRevenue"

    agg_dict = {
        rev_col: "sum",
        "Quantity": "sum",
        "InvoiceNo": "nunique" if "InvoiceNo" in valid.columns else "count",
        "UnitPrice": "mean" if "UnitPrice" in valid.columns else lambda x: 0.0,
    }
    if "StockCode" in valid.columns:
        agg_dict["StockCode"] = "first"

    grouped = valid.groupby("Description").agg(agg_dict).reset_index()
    grouped.rename(columns={
        rev_col: "NetRevenue",
        "InvoiceNo": "Orders",
        "UnitPrice": "AvgPrice",
    }, inplace=True)
    
    grouped["Revenue"] = grouped["NetRevenue"].round(2)
    grouped["NetRevenue"] = grouped["Revenue"]
    grouped["Quantity"] = grouped["Quantity"].astype(int)
    grouped["UnitsSold"] = grouped["Quantity"]
    grouped["AvgPrice"] = grouped["AvgPrice"].round(2)
    if "StockCode" not in grouped.columns:
        grouped["StockCode"] = "SKU"

    top_revenue = grouped.sort_values(by="NetRevenue", ascending=False).head(top_n).copy()
    top_quantity = grouped.sort_values(by="Quantity", ascending=False).head(top_n).copy()

    return {
        "top_revenue": top_revenue.to_dict(orient="records"),
        "top_quantity": top_quantity.to_dict(orient="records"),
    }

@router.get("/geo")
def get_geo(top_n: int = Query(8)):
    df = ds.get_df()
    geo = analyze_geographic_sales(df, top_n=top_n)
    if "Revenue" in geo.columns and "NetRevenue" not in geo.columns:
        geo["NetRevenue"] = geo["Revenue"]
    return geo.to_dict(orient="records")
