"""
Unit tests for business metrics, KPIs, and period-over-period calculations.
"""

from __future__ import annotations

import pandas as pd
import pytest
from src.metrics import compute_executive_kpis, compute_period_over_period


@pytest.fixture
def sample_cleaned_df():
    return pd.DataFrame({
        "InvoiceNo": ["101", "101", "102", "C103", "104"],
        "Quantity": [2, 1, 4, -1, 3],
        "UnitPrice": [10.0, 20.0, 5.0, 10.0, 15.0],
        "NetRevenue": [20.0, 20.0, 20.0, -10.0, 45.0],  # Net total: 95.0
        "GrossRevenue": [20.0, 20.0, 20.0, 0.0, 45.0],   # Gross total: 105.0
        "RefundAmount": [0.0, 0.0, 0.0, 10.0, 0.0],     # Refunds: 10.0
        "CustomerID": ["C1", "C1", "C2", "C1", "C1"],  # C1 has orders 101 and 104 -> repeat customer!
        "Country": ["UK", "UK", "France", "UK", "UK"],
        "IsCancelled": [False, False, False, True, False],
        "InvoiceDate": pd.to_datetime([
            "2023-01-01", "2023-01-01", "2023-01-05", "2023-01-10", "2023-01-20"
        ]),
        "StockCode": ["A", "B", "A", "A", "C"],
        "Description": ["Prod A", "Prod B", "Prod A", "Prod A", "Prod C"],
    })


def test_compute_executive_kpis(sample_cleaned_df):
    kpis = compute_executive_kpis(sample_cleaned_df)

    assert kpis["total_net_revenue"] == 95.0
    assert kpis["total_gross_revenue"] == 105.0
    assert kpis["total_refunds"] == 10.0

    # Non-cancelled invoices: 101, 102, 104 -> 3 orders
    assert kpis["total_orders"] == 3

    # Unique customers: C1 and C2 -> 2
    assert kpis["unique_customers"] == 2

    # Repeat customer rate: C1 has 2 completed orders (101, 104), C2 has 1 -> 1 / 2 = 50.0%
    assert kpis["repeat_customer_rate"] == 50.0

    # Total units sold (positive transactions): 2 + 1 + 4 + 3 = 10
    assert kpis["total_units_sold"] == 10

    # Cancellation rate: 1 cancelled invoice (C103) out of 4 total invoices -> 25.0%
    assert kpis["cancellation_rate"] == 25.0


def test_compute_period_over_period(sample_cleaned_df):
    pop = compute_period_over_period(sample_cleaned_df)
    assert pop["status"] == "valid"
    assert "delta_pct" in pop
    assert "current_value" in pop
    assert "previous_value" in pop


def test_empty_dataframe_metrics():
    empty_df = pd.DataFrame()
    kpis = compute_executive_kpis(empty_df)
    assert kpis["total_net_revenue"] == 0.0
    assert kpis["total_orders"] == 0
    assert kpis["unique_customers"] == 0

    pop = compute_period_over_period(empty_df)
    assert pop["status"] == "insufficient_data"
