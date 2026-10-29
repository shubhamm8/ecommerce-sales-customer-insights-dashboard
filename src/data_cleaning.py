"""
Data Cleaning and Preprocessing Pipeline.

Handles column normalization, type conversions, missing values, duplicates,
anomaly checks, and returns/cancellations categorization according to UCI Online Retail conventions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


STANDARD_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]

# Aliases for automatic schema mapping
COLUMN_MAPPINGS: Dict[str, List[str]] = {
    "InvoiceNo": [
        "invoiceno",
        "invoice_no",
        "invoice",
        "invoicenumber",
        "order_id",
        "orderid",
        "transaction_id",
        "bill_no",
    ],
    "StockCode": [
        "stockcode",
        "stock_code",
        "sku",
        "product_id",
        "productid",
        "item_code",
        "item_id",
    ],
    "Description": [
        "description",
        "desc",
        "product_name",
        "item_name",
        "product_description",
        "item_description",
        "title",
    ],
    "Quantity": [
        "quantity",
        "qty",
        "units",
        "volume",
        "amount_ordered",
        "count",
    ],
    "InvoiceDate": [
        "invoicedate",
        "invoice_date",
        "order_date",
        "date",
        "timestamp",
        "transaction_date",
        "datetime",
    ],
    "UnitPrice": [
        "unitprice",
        "unit_price",
        "price",
        "price_per_unit",
        "cost_per_unit",
        "rate",
        "item_price",
    ],
    "CustomerID": [
        "customerid",
        "customer_id",
        "client_id",
        "user_id",
        "buyer_id",
        "account_id",
    ],
    "Country": [
        "country",
        "region",
        "state",
        "location",
        "nation",
        "country_code",
    ],
}


def map_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Standardize DataFrame column names using fuzzy/alias mapping.

    Returns:
        Mapped DataFrame copy and a dictionary mapping original -> standardized names.
    """
    df = df.copy()
    raw_cols = {col: str(col).strip() for col in df.columns}
    rename_dict: Dict[str, str] = {}

    for orig_col, cleaned_name in raw_cols.items():
        norm = re.sub(r"[^a-z0-9]", "", cleaned_name.lower())
        matched = False
        for target, aliases in COLUMN_MAPPINGS.items():
            norm_target = target.lower()
            norm_aliases = [re.sub(r"[^a-z0-9]", "", a.lower()) for a in aliases]
            if norm == norm_target or norm in norm_aliases:
                rename_dict[orig_col] = target
                matched = True
                break
        if not matched:
            rename_dict[orig_col] = cleaned_name

    df = df.rename(columns=rename_dict)
    return df, rename_dict


def validate_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate presence of essential e-commerce fields.
    """
    present_cols = list(df.columns)
    missing_required = []
    missing_optional = []

    # Hard requirements for any financial analytics
    for req in ["Quantity", "UnitPrice", "InvoiceDate"]:
        if req not in present_cols:
            missing_required.append(req)

    for opt in ["InvoiceNo", "StockCode", "Description", "CustomerID", "Country"]:
        if opt not in present_cols:
            missing_optional.append(opt)

    is_valid = len(missing_required) == 0
    return {
        "is_valid": is_valid,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "has_customer_id": "CustomerID" in present_cols,
        "has_invoice_no": "InvoiceNo" in present_cols,
        "has_products": "StockCode" in present_cols or "Description" in present_cols,
        "has_country": "Country" in present_cols,
    }


def clean_ecommerce_data(
    df: pd.DataFrame,
    remove_duplicates: bool = True,
    impute_missing_descriptions: bool = True,
    flag_cancellations: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    End-to-end data cleaning pipeline for e-commerce transactions.

    Returns:
        (cleaned_df, cleaning_summary_dict)
    """
    summary: Dict[str, Any] = {
        "initial_rows": int(len(df)),
        "initial_columns": list(df.columns),
        "duplicates_removed": 0,
        "missing_customer_ids": 0,
        "missing_descriptions": 0,
        "cancellations_count": 0,
        "zero_or_negative_price_rows": 0,
        "final_rows": 0,
        "date_range": None,
    }

    if df.empty:
        summary["final_rows"] = 0
        return df.copy(), summary

    # Standardize column names
    cleaned, _ = map_columns(df)

    # Missing value initial assessment
    if "CustomerID" in cleaned.columns:
        summary["missing_customer_ids"] = int(cleaned["CustomerID"].isna().sum())
    if "Description" in cleaned.columns:
        summary["missing_descriptions"] = int(cleaned["Description"].isna().sum())

    # Handle duplicates
    if remove_duplicates:
        dup_mask = cleaned.duplicated()
        summary["duplicates_removed"] = int(dup_mask.sum())
        cleaned = cleaned.drop_duplicates().copy()

    # Numeric conversion
    if "Quantity" in cleaned.columns:
        cleaned["Quantity"] = pd.to_numeric(cleaned["Quantity"], errors="coerce").fillna(0).astype(float)

    if "UnitPrice" in cleaned.columns:
        cleaned["UnitPrice"] = pd.to_numeric(cleaned["UnitPrice"], errors="coerce").fillna(0.0).astype(float)
        invalid_price_mask = cleaned["UnitPrice"] <= 0
        summary["zero_or_negative_price_rows"] = int(invalid_price_mask.sum())
        # We retain non-negative prices for normal transactions, filter out zero price gifts if needed
        # In retail analytics, UnitPrice <= 0 usually represents bad entries, gifts, or adjustments
        cleaned = cleaned[cleaned["UnitPrice"] > 0].copy()

    # Date parsing
    if "InvoiceDate" in cleaned.columns:
        cleaned["InvoiceDate"] = pd.to_datetime(cleaned["InvoiceDate"], errors="coerce")
        # Drop rows where date couldn't be parsed
        valid_dates = cleaned["InvoiceDate"].notna()
        cleaned = cleaned[valid_dates].copy()
        if not cleaned.empty:
            summary["date_range"] = (
                cleaned["InvoiceDate"].min().strftime("%Y-%m-%d"),
                cleaned["InvoiceDate"].max().strftime("%Y-%m-%d"),
            )

    # Standardize Description
    if "Description" in cleaned.columns:
        cleaned["Description"] = cleaned["Description"].astype(str).str.strip()
        if impute_missing_descriptions:
            cleaned.loc[cleaned["Description"].str.lower().isin(["nan", "none", "", "null"]), "Description"] = "Unknown Product"

    # Standardize StockCode
    if "StockCode" in cleaned.columns:
        cleaned["StockCode"] = cleaned["StockCode"].astype(str).str.strip().str.upper()

    # Standardize CustomerID
    if "CustomerID" in cleaned.columns:
        # Convert floats like 12345.0 to integer strings "12345" while preserving None
        cleaned["CustomerID"] = cleaned["CustomerID"].apply(
            lambda x: str(int(float(x))) if pd.notna(x) and str(x).replace(".", "", 1).isdigit() else (None if pd.isna(x) or str(x).lower() in ["nan", "none", ""] else str(x).strip())
        )

    # Standardize Country
    if "Country" in cleaned.columns:
        cleaned["Country"] = cleaned["Country"].astype(str).str.strip().str.title()
        cleaned.loc[cleaned["Country"].isin(["Nan", "None", "", "Null"]), "Country"] = "Unspecified"
    else:
        cleaned["Country"] = "Unspecified"

    # Identify and flag cancellations / refunds
    cleaned["IsCancelled"] = False
    if flag_cancellations:
        cancellation_mask = pd.Series(False, index=cleaned.index)
        if "InvoiceNo" in cleaned.columns:
            invoice_str = cleaned["InvoiceNo"].astype(str).str.strip()
            cancellation_mask = cancellation_mask | invoice_str.str.startswith(("C", "c"))
        if "Quantity" in cleaned.columns:
            cancellation_mask = cancellation_mask | (cleaned["Quantity"] < 0)

        cleaned["IsCancelled"] = cancellation_mask
        summary["cancellations_count"] = int(cancellation_mask.sum())

    # Derived transaction metrics
    if "Quantity" in cleaned.columns and "UnitPrice" in cleaned.columns:
        cleaned["LineTotal"] = cleaned["Quantity"] * cleaned["UnitPrice"]
        # Gross sales (only positive quantities)
        cleaned["GrossRevenue"] = np.where(cleaned["Quantity"] > 0, cleaned["LineTotal"], 0.0)
        # Refund/return value (absolute amount of negative quantities)
        cleaned["RefundAmount"] = np.where(cleaned["Quantity"] < 0, np.abs(cleaned["LineTotal"]), 0.0)
        # Net revenue
        cleaned["NetRevenue"] = cleaned["LineTotal"]

    summary["final_rows"] = int(len(cleaned))
    return cleaned, summary
