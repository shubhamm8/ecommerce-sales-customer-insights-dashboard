"""
Sales Analytics Module.

Performs:
- Time-series aggregation (daily, weekly, monthly).
- Product performance analysis (top/bottom revenue, volume, average unit price).
- Geographic performance distribution.
- Day-of-week and hourly transaction patterns.
- Revenue concentration analysis.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd


def aggregate_sales_time_series(
    df: pd.DataFrame,
    freq: str = "D",
    date_col: str = "InvoiceDate",
    value_col: str = "NetRevenue",
) -> pd.DataFrame:
    """
    Aggregate transaction sales into a contiguous time series.
    Supported frequencies: 'D' (daily), 'W' (weekly), 'M' (monthly).
    """
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(columns=["Date", "Revenue", "OrderCount", "UnitsSold"])

    data = df.dropna(subset=[date_col]).copy()
    data["Date"] = data[date_col].dt.to_period(freq).dt.to_timestamp()

    # Aggregate
    grouped = data.groupby("Date").agg(
        Revenue=(value_col, "sum"),
        UnitsSold=("Quantity", lambda x: int(x[x > 0].sum()) if "Quantity" in data.columns else len(x)),
        OrderCount=("InvoiceNo", "nunique") if "InvoiceNo" in data.columns else ("Date", "count"),
    ).reset_index()

    # Fill date gaps with 0 for daily frequency
    if freq == "D" and not grouped.empty and len(grouped) > 1:
        full_idx = pd.date_range(start=grouped["Date"].min(), end=grouped["Date"].max(), freq="D")
        grouped = grouped.set_index("Date").reindex(full_idx, fill_value=0).rename_axis("Date").reset_index()

    grouped["Revenue"] = grouped["Revenue"].round(2)
    return grouped


def analyze_product_performance(
    df: pd.DataFrame,
    top_n: int = 10,
) -> Dict[str, pd.DataFrame]:
    """
    Analyze product rankings by revenue and quantity sold.
    """
    if df.empty or "Description" not in df.columns:
        empty = pd.DataFrame(columns=["Description", "Revenue", "UnitsSold", "OrderCount", "AvgPrice"])
        return {"top_revenue": empty, "bottom_revenue": empty, "all_products": empty}

    valid = df[df.get("Quantity", 1) > 0].copy()
    rev_col = "NetRevenue" if "NetRevenue" in valid.columns else ("LineTotal" if "LineTotal" in valid.columns else None)

    if rev_col is None:
        valid["ComputedRevenue"] = valid["Quantity"] * valid.get("UnitPrice", 1.0)
        rev_col = "ComputedRevenue"

    grouped = valid.groupby("Description").agg(
        Revenue=(rev_col, "sum"),
        UnitsSold=("Quantity", "sum") if "Quantity" in valid.columns else ("Description", "count"),
        OrderCount=("InvoiceNo", "nunique") if "InvoiceNo" in valid.columns else ("Description", "count"),
        AvgPrice=("UnitPrice", "mean") if "UnitPrice" in valid.columns else ("Description", lambda x: 0.0),
    ).reset_index()

    grouped["Revenue"] = grouped["Revenue"].round(2)
    grouped["AvgPrice"] = grouped["AvgPrice"].round(2)
    grouped = grouped.sort_values(by="Revenue", ascending=False)

    top_revenue = grouped.head(top_n).copy()
    bottom_revenue = grouped[grouped["Revenue"] > 0].tail(top_n).sort_values(by="Revenue", ascending=True).copy()

    return {
        "top_revenue": top_revenue,
        "bottom_revenue": bottom_revenue,
        "all_products": grouped,
    }


def analyze_geographic_sales(
    df: pd.DataFrame,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Compute sales breakdown by Country.
    """
    if df.empty or "Country" not in df.columns:
        return pd.DataFrame(columns=["Country", "Revenue", "OrderCount", "CustomerCount", "RevenueSharePct"])

    rev_col = "NetRevenue" if "NetRevenue" in df.columns else "LineTotal"
    if rev_col not in df.columns and "Quantity" in df.columns and "UnitPrice" in df.columns:
        df = df.copy()
        df["NetRevenue"] = df["Quantity"] * df["UnitPrice"]
        rev_col = "NetRevenue"

    grouped = df.groupby("Country").agg(
        Revenue=(rev_col, "sum"),
        OrderCount=("InvoiceNo", "nunique") if "InvoiceNo" in df.columns else ("Country", "count"),
        CustomerCount=("CustomerID", lambda x: x.dropna().nunique()) if "CustomerID" in df.columns else ("Country", lambda x: 0),
    ).reset_index()

    total_rev = grouped["Revenue"].sum()
    grouped["RevenueSharePct"] = ((grouped["Revenue"] / total_rev) * 100.0).round(2) if total_rev > 0 else 0.0
    grouped["Revenue"] = grouped["Revenue"].round(2)

    return grouped.sort_values(by="Revenue", ascending=False).head(top_n)


def analyze_temporal_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Extract Day of Week and Hour of Day transaction volume and revenue distributions.
    """
    if df.empty or "InvoiceDate" not in df.columns:
        return {
            "day_of_week": pd.DataFrame(columns=["DayOfWeek", "Revenue", "OrderCount"]),
            "hour_of_day": pd.DataFrame(columns=["Hour", "Revenue", "OrderCount"]),
        }

    valid = df.dropna(subset=["InvoiceDate"]).copy()
    rev_col = "NetRevenue" if "NetRevenue" in valid.columns else "Quantity"

    valid["DayOfWeek"] = valid["InvoiceDate"].dt.day_name()
    valid["Hour"] = valid["InvoiceDate"].dt.hour

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    dow = valid.groupby("DayOfWeek").agg(
        Revenue=(rev_col, "sum"),
        OrderCount=("InvoiceNo", "nunique") if "InvoiceNo" in valid.columns else ("DayOfWeek", "count"),
    ).reindex(day_order).fillna(0).reset_index()

    hod = valid.groupby("Hour").agg(
        Revenue=(rev_col, "sum"),
        OrderCount=("InvoiceNo", "nunique") if "InvoiceNo" in valid.columns else ("Hour", "count"),
    ).reindex(range(24)).fillna(0).reset_index()

    dow["Revenue"] = dow["Revenue"].round(2)
    hod["Revenue"] = hod["Revenue"].round(2)

    return {"day_of_week": dow, "hour_of_day": hod}
