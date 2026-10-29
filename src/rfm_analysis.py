"""
RFM (Recency, Frequency, Monetary) Feature Engineering Module.

Extracts customer behavioral attributes:
- Recency: Days since most recent qualifying order relative to benchmark reference date.
- Frequency: Count of distinct qualifying orders.
- Monetary: Net spend on qualifying transactions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import pandas as pd


def compute_rfm_table(
    df: pd.DataFrame,
    reference_date: Optional[datetime] = None,
    include_returns_in_monetary: bool = True,
) -> pd.DataFrame:
    """
    Calculate Recency, Frequency, and Monetary metrics per unique CustomerID.
    """
    if df.empty or "CustomerID" not in df.columns or "InvoiceDate" not in df.columns:
        return pd.DataFrame(columns=["CustomerID", "Recency", "Frequency", "Monetary"])

    # Filter out missing customer IDs
    valid = df[df["CustomerID"].notna() & (df["CustomerID"] != "")].copy()
    if valid.empty:
        return pd.DataFrame(columns=["CustomerID", "Recency", "Frequency", "Monetary"])

    # Benchmark analysis date: default to 1 day after the latest transaction
    max_txn_date = valid["InvoiceDate"].max()
    if reference_date is None:
        ref_date = max_txn_date + pd.Timedelta(days=1)
    else:
        ref_date = reference_date

    # Revenue column
    if "NetRevenue" not in valid.columns:
        valid["NetRevenue"] = valid["Quantity"] * valid.get("UnitPrice", 1.0)

    # Only positive orders count toward Recency and Frequency qualifying transactions
    qualifying_orders = valid[valid.get("Quantity", 1) > 0].copy()

    # If all records are returns/cancellations
    if qualifying_orders.empty:
        qualifying_orders = valid.copy()

    # Aggregate Recency and Frequency from qualifying orders
    rf_grouped = qualifying_orders.groupby("CustomerID").agg(
        LastOrder=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique") if "InvoiceNo" in qualifying_orders.columns else ("CustomerID", "count"),
    ).reset_index()

    rf_grouped["Recency"] = (ref_date - rf_grouped["LastOrder"]).dt.days
    rf_grouped["Recency"] = rf_grouped["Recency"].clip(lower=0)

    # Monetary value: optionally account for returns/refunds for accurate net value
    if include_returns_in_monetary:
        m_grouped = valid.groupby("CustomerID")["NetRevenue"].sum().reset_index()
        m_grouped = m_grouped.rename(columns={"NetRevenue": "Monetary"})
    else:
        m_grouped = qualifying_orders.groupby("CustomerID")["NetRevenue"].sum().reset_index()
        m_grouped = m_grouped.rename(columns={"NetRevenue": "Monetary"})

    rfm = pd.merge(rf_grouped[["CustomerID", "Recency", "Frequency"]], m_grouped, on="CustomerID", how="inner")

    # Round numerical columns
    rfm["Monetary"] = rfm["Monetary"].round(2)
    rfm["Frequency"] = rfm["Frequency"].astype(int)
    rfm["Recency"] = rfm["Recency"].astype(int)

    # Filter out customers with zero or negative total monetary value for clustering stability
    rfm = rfm[rfm["Monetary"] > 0].copy()

    return rfm.sort_values(by="Monetary", ascending=False).reset_index(drop=True)


def calculate_rfm_scores(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate quantile-based heuristic RFM scores (1 to 5) for quick rule-based categorization.
    Note: Lower recency receives higher score (5 = most recent).
    """
    if len(rfm_df) < 5:
        df = rfm_df.copy()
        df["R_Score"] = 3
        df["F_Score"] = 3
        df["M_Score"] = 3
        df["RFM_Score"] = "333"
        return df

    df = rfm_df.copy()

    # Recency: lower is better -> invert ranks
    try:
        df["R_Score"] = pd.qcut(df["Recency"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    except Exception:
        df["R_Score"] = 3

    # Frequency: higher is better
    try:
        df["F_Score"] = pd.qcut(df["Frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    except Exception:
        df["F_Score"] = 3

    # Monetary: higher is better
    try:
        df["M_Score"] = pd.qcut(df["Monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    except Exception:
        df["M_Score"] = 3

    df["RFM_Score"] = df["R_Score"].astype(str) + df["F_Score"].astype(str) + df["M_Score"].astype(str)
    return df
