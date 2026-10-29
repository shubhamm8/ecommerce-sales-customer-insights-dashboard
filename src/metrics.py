"""
Core Business Metrics and KPI Computation Engine.

Provides transparent, strictly calculated metrics:
- Gross Revenue, Net Revenue, Refund Total
- Distinct Order Count, Unique Customer Count
- Average Order Value (AOV), Units Sold
- Repeat Customer Rate, Cancellation Rate
- Period-over-Period comparisons
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd


def compute_executive_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute comprehensive business health KPIs from a cleaned transaction DataFrame.
    """
    if df.empty:
        return {
            "total_net_revenue": 0.0,
            "total_gross_revenue": 0.0,
            "total_refunds": 0.0,
            "total_orders": 0,
            "total_units_sold": 0,
            "unique_customers": 0,
            "average_order_value": 0.0,
            "repeat_customer_rate": 0.0,
            "cancellation_rate": 0.0,
            "total_skus": 0,
            "total_countries": 0,
        }

    # Revenue metrics
    if "NetRevenue" in df.columns:
        net_revenue = float(df["NetRevenue"].sum())
        gross_revenue = float(df["GrossRevenue"].sum()) if "GrossRevenue" in df.columns else float(df[df["Quantity"] > 0]["NetRevenue"].sum())
        refunds = float(df["RefundAmount"].sum()) if "RefundAmount" in df.columns else float(np.abs(df[df["Quantity"] < 0]["NetRevenue"].sum()))
    elif "Quantity" in df.columns and "UnitPrice" in df.columns:
        line_total = df["Quantity"] * df["UnitPrice"]
        net_revenue = float(line_total.sum())
        gross_revenue = float(line_total[df["Quantity"] > 0].sum())
        refunds = float(np.abs(line_total[df["Quantity"] < 0].sum()))
    else:
        net_revenue = 0.0
        gross_revenue = 0.0
        refunds = 0.0

    # Orders count: distinct non-cancelled invoices
    if "InvoiceNo" in df.columns:
        if "IsCancelled" in df.columns:
            valid_orders = df[~df["IsCancelled"]]["InvoiceNo"].nunique()
            cancelled_invoices = df[df["IsCancelled"]]["InvoiceNo"].nunique()
            total_invoices = df["InvoiceNo"].nunique()
        else:
            valid_orders = df[df["Quantity"] > 0]["InvoiceNo"].nunique()
            cancelled_invoices = df[df["Quantity"] <= 0]["InvoiceNo"].nunique()
            total_invoices = df["InvoiceNo"].nunique()
    else:
        valid_orders = len(df[df["Quantity"] > 0]) if "Quantity" in df.columns else len(df)
        cancelled_invoices = 0
        total_invoices = len(df)

    cancellation_rate = (cancelled_invoices / total_invoices * 100.0) if total_invoices > 0 else 0.0

    # Units sold (positive transactions only)
    if "Quantity" in df.columns:
        units_sold = int(df[df["Quantity"] > 0]["Quantity"].sum())
    else:
        units_sold = 0

    # Customer metrics
    if "CustomerID" in df.columns:
        cust_series = df["CustomerID"].dropna()
        cust_series = cust_series[cust_series != ""]
        unique_customers = int(cust_series.nunique())

        # Repeat customer rate (customers with >= 2 distinct completed orders)
        if "InvoiceNo" in df.columns:
            if "IsCancelled" in df.columns:
                valid_mask = ~df["IsCancelled"]
            elif "Quantity" in df.columns:
                valid_mask = df["Quantity"] > 0
            else:
                valid_mask = pd.Series(True, index=df.index)
            order_counts = df[valid_mask].groupby("CustomerID")["InvoiceNo"].nunique()
            repeat_count = int((order_counts > 1).sum())
            repeat_rate = (repeat_count / unique_customers * 100.0) if unique_customers > 0 else 0.0
        else:
            repeat_rate = 0.0
    else:
        unique_customers = 0
        repeat_rate = 0.0

    # Average Order Value (AOV = Gross Revenue / Valid Orders)
    aov = (gross_revenue / valid_orders) if valid_orders > 0 else 0.0

    total_skus = df["StockCode"].nunique() if "StockCode" in df.columns else (df["Description"].nunique() if "Description" in df.columns else 0)
    total_countries = df["Country"].nunique() if "Country" in df.columns else 0

    return {
        "total_net_revenue": round(net_revenue, 2),
        "total_gross_revenue": round(gross_revenue, 2),
        "total_refunds": round(refunds, 2),
        "total_orders": int(valid_orders),
        "total_units_sold": units_sold,
        "unique_customers": unique_customers,
        "average_order_value": round(aov, 2),
        "repeat_customer_rate": round(repeat_rate, 2),
        "cancellation_rate": round(cancellation_rate, 2),
        "total_skus": int(total_skus),
        "total_countries": int(total_countries),
    }


def compute_period_over_period(
    df: pd.DataFrame,
    date_col: str = "InvoiceDate",
    value_col: str = "NetRevenue",
) -> Dict[str, Any]:
    """
    Compare current period to previous equal-duration period.
    """
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return {"delta_pct": 0.0, "current_value": 0.0, "previous_value": 0.0, "status": "insufficient_data"}

    valid = df.dropna(subset=[date_col, value_col]).sort_values(date_col)
    if len(valid) < 4:
        return {"delta_pct": 0.0, "current_value": 0.0, "previous_value": 0.0, "status": "insufficient_data"}

    min_date = valid[date_col].min()
    max_date = valid[date_col].max()
    span = max_date - min_date

    if span.days < 2:
        return {"delta_pct": 0.0, "current_value": 0.0, "previous_value": 0.0, "status": "insufficient_history"}

    midpoint = min_date + (span / 2)
    prev_period = valid[valid[date_col] < midpoint]
    curr_period = valid[valid[date_col] >= midpoint]

    prev_val = float(prev_period[value_col].sum())
    curr_val = float(curr_period[value_col].sum())

    if prev_val == 0:
        delta_pct = 100.0 if curr_val > 0 else 0.0
    else:
        delta_pct = ((curr_val - prev_val) / abs(prev_val)) * 100.0

    return {
        "delta_pct": round(delta_pct, 2),
        "current_value": round(curr_val, 2),
        "previous_value": round(prev_val, 2),
        "period_midpoint": midpoint.strftime("%Y-%m-%d"),
        "status": "valid",
    }
