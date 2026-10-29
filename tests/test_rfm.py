"""
Unit tests for RFM feature engineering.
"""

from __future__ import annotations

from datetime import datetime
import pandas as pd
import pytest
from src.rfm_analysis import calculate_rfm_scores, compute_rfm_table


@pytest.fixture
def rfm_sample_df():
    return pd.DataFrame({
        "InvoiceNo": ["100", "101", "102", "103", "C104"],
        "InvoiceDate": pd.to_datetime([
            "2023-01-01", "2023-01-10", "2023-01-15", "2023-01-20", "2023-01-25"
        ]),
        "CustomerID": ["10001", "10001", "10002", "10003", "10003"],
        "Quantity": [2, 3, 5, 4, -1],
        "UnitPrice": [10.0, 10.0, 20.0, 15.0, 15.0],
        "NetRevenue": [20.0, 30.0, 100.0, 60.0, -15.0],
    })


def test_compute_rfm_table_values(rfm_sample_df):
    ref_date = datetime(2023, 1, 30)
    rfm = compute_rfm_table(rfm_sample_df, reference_date=ref_date)

    assert len(rfm) == 3

    # Customer 10001: Last order 2023-01-10. Days from Jan 30 = 20. Orders: 2. Spend: 50.0
    c1 = rfm[rfm["CustomerID"] == "10001"].iloc[0]
    assert c1["Recency"] == 20
    assert c1["Frequency"] == 2
    assert c1["Monetary"] == 50.0

    # Customer 10002: Last order 2023-01-15. Days from Jan 30 = 15. Orders: 1. Spend: 100.0
    c2 = rfm[rfm["CustomerID"] == "10002"].iloc[0]
    assert c2["Recency"] == 15
    assert c2["Frequency"] == 1
    assert c2["Monetary"] == 100.0

    # Customer 10003: Last positive order 2023-01-20. Days = 10. Orders: 1. Spend: 60 - 15 = 45.0
    c3 = rfm[rfm["CustomerID"] == "10003"].iloc[0]
    assert c3["Recency"] == 10
    assert c3["Frequency"] == 1
    assert c3["Monetary"] == 45.0


def test_rfm_missing_customer_id():
    df_missing = pd.DataFrame({
        "InvoiceNo": ["100", "101"],
        "InvoiceDate": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        "CustomerID": [None, ""],
        "Quantity": [1, 2],
        "UnitPrice": [10.0, 20.0],
        "NetRevenue": [10.0, 40.0],
    })
    rfm = compute_rfm_table(df_missing)
    assert rfm.empty


def test_calculate_rfm_scores(rfm_sample_df):
    rfm = compute_rfm_table(rfm_sample_df)
    scored = calculate_rfm_scores(rfm)
    assert "R_Score" in scored.columns
    assert "F_Score" in scored.columns
    assert "M_Score" in scored.columns
    assert "RFM_Score" in scored.columns
