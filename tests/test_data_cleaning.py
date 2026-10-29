"""
Unit tests for data cleaning and schema validation pipeline.
"""

from __future__ import annotations

import pandas as pd
import pytest
from src.data_cleaning import clean_ecommerce_data, map_columns, validate_schema


@pytest.fixture
def sample_raw_dataframe():
    return pd.DataFrame({
        "invoice_no": ["536365", "536365", "C536366", "536367", "536367"],
        "stock_code": ["85123A", "71053", "85123A", "22752", "22752"],
        "description": ["WHITE HEART", "METAL LANTERN", "WHITE HEART", "BOXES", "BOXES"],
        "quantity": [6, 2, -1, 10, 10],  # row 5 is duplicate of row 4
        "invoice_date": ["2023-01-01 08:26:00", "2023-01-01 08:30:00", "2023-01-02 09:00:00", "2023-01-03 10:00:00", "2023-01-03 10:00:00"],
        "unit_price": [2.55, 3.39, 2.55, 7.65, 7.65],
        "customer_id": [17850.0, 17850.0, 17850.0, None, None],
        "country": ["United Kingdom", "United Kingdom", "United Kingdom", "France", "France"],
    })


def test_map_columns(sample_raw_dataframe):
    mapped, rename_dict = map_columns(sample_raw_dataframe)
    assert "InvoiceNo" in mapped.columns
    assert "StockCode" in mapped.columns
    assert "Description" in mapped.columns
    assert "Quantity" in mapped.columns
    assert "InvoiceDate" in mapped.columns
    assert "UnitPrice" in mapped.columns
    assert "CustomerID" in mapped.columns
    assert "Country" in mapped.columns


def test_validate_schema(sample_raw_dataframe):
    mapped, _ = map_columns(sample_raw_dataframe)
    report = validate_schema(mapped)
    assert report["is_valid"] is True
    assert report["has_customer_id"] is True
    assert report["has_invoice_no"] is True


def test_clean_ecommerce_data_duplicates_and_cancellations(sample_raw_dataframe):
    cleaned, summary = clean_ecommerce_data(sample_raw_dataframe)

    # Duplicate row should be removed (5 rows -> 4 rows)
    assert summary["duplicates_removed"] == 1
    assert len(cleaned) == 4

    # Cancellation check
    assert summary["cancellations_count"] == 1
    cancelled_rows = cleaned[cleaned["IsCancelled"]]
    assert len(cancelled_rows) == 1
    assert cancelled_rows.iloc[0]["InvoiceNo"] == "C536366"
    assert cancelled_rows.iloc[0]["Quantity"] == -1.0


def test_clean_ecommerce_data_negative_and_zero_price():
    df_invalid_price = pd.DataFrame({
        "InvoiceNo": ["1001", "1002", "1003"],
        "StockCode": ["A", "B", "C"],
        "Description": ["Item A", "Item B", "Item C"],
        "Quantity": [1, 2, 3],
        "InvoiceDate": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "UnitPrice": [10.0, 0.0, -5.0],
        "CustomerID": ["123", "124", "125"],
        "Country": ["UK", "UK", "UK"],
    })

    cleaned, summary = clean_ecommerce_data(df_invalid_price)
    # Zero and negative price rows should be removed
    assert summary["zero_or_negative_price_rows"] == 2
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["StockCode"] == "A"


def test_clean_ecommerce_data_empty():
    empty_df = pd.DataFrame()
    cleaned, summary = clean_ecommerce_data(empty_df)
    assert cleaned.empty
    assert summary["final_rows"] == 0
