"""
Customer Analytics Module.

Performs:
- Customer lifetime value and spend aggregation.
- Pareto (80/20) revenue concentration analysis.
- Guest vs identified checkout distribution.
- Top customer rankings.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def compute_customer_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate transactional metrics to the customer level.
    """
    if df.empty or "CustomerID" not in df.columns:
        return pd.DataFrame(columns=[
            "CustomerID", "TotalSpend", "OrderCount", "TotalUnits", "AvgOrderValue",
            "FirstPurchase", "LastPurchase", "TenureDays", "Country"
        ])

    # Only include identified customers
    valid = df[df["CustomerID"].notna() & (df["CustomerID"] != "")].copy()
    if valid.empty:
        return pd.DataFrame()

    rev_col = "NetRevenue" if "NetRevenue" in valid.columns else "LineTotal"
    if rev_col not in valid.columns and "Quantity" in valid.columns and "UnitPrice" in valid.columns:
        valid["NetRevenue"] = valid["Quantity"] * valid["UnitPrice"]
        rev_col = "NetRevenue"

    # Positive qualifying orders only for spend, but aggregate total net
    grouped = valid.groupby("CustomerID").agg(
        TotalSpend=(rev_col, "sum"),
        OrderCount=("InvoiceNo", "nunique") if "InvoiceNo" in valid.columns else (rev_col, "count"),
        TotalUnits=("Quantity", lambda x: int(x[x > 0].sum()) if "Quantity" in valid.columns else len(x)),
        FirstPurchase=("InvoiceDate", "min") if "InvoiceDate" in valid.columns else (rev_col, lambda x: None),
        LastPurchase=("InvoiceDate", "max") if "InvoiceDate" in valid.columns else (rev_col, lambda x: None),
        Country=("Country", lambda x: x.mode().iloc[0] if not x.empty and not x.isna().all() else "Unspecified"),
    ).reset_index()

    grouped["TotalSpend"] = grouped["TotalSpend"].round(2)
    grouped["AvgOrderValue"] = np.where(
        grouped["OrderCount"] > 0,
        (grouped["TotalSpend"] / grouped["OrderCount"]).round(2),
        0.0
    )

    if "FirstPurchase" in grouped.columns and "LastPurchase" in grouped.columns:
        grouped["TenureDays"] = (grouped["LastPurchase"] - grouped["FirstPurchase"]).dt.days
    else:
        grouped["TenureDays"] = 0

    return grouped.sort_values(by="TotalSpend", ascending=False)


def analyze_pareto_concentration(customer_summary: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze revenue concentration among top customers (Pareto Principle).
    """
    if customer_summary.empty or "TotalSpend" not in customer_summary.columns:
        return {
            "top_20_pct_revenue_share": 0.0,
            "top_10_pct_revenue_share": 0.0,
            "top_5_pct_revenue_share": 0.0,
            "total_customer_revenue": 0.0,
            "gini_coefficient": 0.0,
        }

    positive_spenders = customer_summary[customer_summary["TotalSpend"] > 0].copy()
    if positive_spenders.empty:
        return {
            "top_20_pct_revenue_share": 0.0,
            "top_10_pct_revenue_share": 0.0,
            "top_5_pct_revenue_share": 0.0,
            "total_customer_revenue": 0.0,
            "gini_coefficient": 0.0,
        }

    positive_spenders = positive_spenders.sort_values(by="TotalSpend", ascending=False)
    total_rev = positive_spenders["TotalSpend"].sum()
    n_cust = len(positive_spenders)

    top_20_idx = max(1, int(n_cust * 0.20))
    top_10_idx = max(1, int(n_cust * 0.10))
    top_5_idx = max(1, int(n_cust * 0.05))

    top_20_share = (positive_spenders.iloc[:top_20_idx]["TotalSpend"].sum() / total_rev) * 100.0
    top_10_share = (positive_spenders.iloc[:top_10_idx]["TotalSpend"].sum() / total_rev) * 100.0
    top_5_share = (positive_spenders.iloc[:top_5_idx]["TotalSpend"].sum() / total_rev) * 100.0

    # Approximate Gini Coefficient
    spend_values = np.sort(positive_spenders["TotalSpend"].values)
    index = np.arange(1, n_cust + 1)
    gini = float((np.sum((2 * index - n_cust - 1) * spend_values)) / (n_cust * np.sum(spend_values)))

    return {
        "top_20_pct_revenue_share": round(float(top_20_share), 2),
        "top_10_pct_revenue_share": round(float(top_10_share), 2),
        "top_5_pct_revenue_share": round(float(top_5_share), 2),
        "total_customer_revenue": round(float(total_rev), 2),
        "gini_coefficient": round(float(gini), 3),
    }
