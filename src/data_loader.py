"""
Data Loading and Synthetic Data Generation Module.

Supports:
- CSV & Excel file loading with automatic encoding detection.
- Generation of realistic, benchmark-aligned synthetic e-commerce data (modeled after UCI Online Retail).
- Persistence and caching utilities.
"""

from __future__ import annotations

import io
import os
from datetime import datetime, timedelta
from typing import Optional, Union

import numpy as np
import pandas as pd


SAMPLE_PRODUCTS = [
    ("85123A", "WHITE HANGING HEART T-LIGHT HOLDER", 2.55, "Home & Decor"),
    ("71053", "WHITE METAL LANTERN", 3.39, "Home & Decor"),
    ("84406B", "CREAM CUPID HEARTS COAT HANGER", 2.75, "Home & Decor"),
    ("84029G", "KNITTED UNION FLAG HOT WATER BOTTLE", 3.39, "Seasonal"),
    ("84029E", "RED WOOLLY HOTTIE WHITE HEART.", 3.39, "Seasonal"),
    ("22752", "SET 7 BABUSHKA NESTING BOXES", 7.65, "Gifts"),
    ("21730", "GLASS STAR FROSTED T-LIGHT HOLDER", 4.25, "Home & Decor"),
    ("22633", "HAND WARMER UNION JACK", 1.85, "Accessories"),
    ("22632", "HAND WARMER RED RETROSPOT", 1.85, "Accessories"),
    ("84879", "ASSORTED COLOUR BIRD ORNAMENT", 1.69, "Gifts"),
    ("22745", "POPPY'S PLAYHOUSE BEDROOM", 2.10, "Toys & Games"),
    ("22748", "POPPY'S PLAYHOUSE KITCHEN", 2.10, "Toys & Games"),
    ("22749", "POPPY'S PLAYHOUSE LIVINGROOM", 2.10, "Toys & Games"),
    ("22310", "IVORY KNITTED MUG COSY", 1.65, "Kitchen"),
    ("84969", "BOX OF 6 ASSORTED COLOUR TEASPOONS", 4.25, "Kitchen"),
    ("20725", "LUNCH BAG RED RETROSPOT", 1.65, "Bags & Luggage"),
    ("20727", "LUNCH BAG BLACK SKULL.", 1.65, "Bags & Luggage"),
    ("20728", "LUNCH BAG CARS BLUE", 1.65, "Bags & Luggage"),
    ("22383", "LUNCH BAG SUKI DESIGN", 1.65, "Bags & Luggage"),
    ("22384", "LUNCH BAG PINK POLKADOT", 1.65, "Bags & Luggage"),
    ("20726", "LUNCH BAG WOODLAND", 1.65, "Bags & Luggage"),
    ("23203", "JUMBO BAG DOILEY PATTERNS", 1.95, "Bags & Luggage"),
    ("20685", "DOORMAT RED RETROSPOT", 7.95, "Home & Decor"),
    ("47566", "PARTY BUNTING", 4.65, "Party Supplies"),
    ("22423", "REGENCY CAKESTAND 3 TIER", 10.95, "Kitchen"),
]

SAMPLE_COUNTRIES = [
    ("United Kingdom", 0.78),
    ("Germany", 0.07),
    ("France", 0.05),
    ("EIRE", 0.03),
    ("Spain", 0.02),
    ("Netherlands", 0.02),
    ("Australia", 0.015),
    ("USA", 0.015),
]


def generate_synthetic_ecommerce_data(
    num_records: int = 2500,
    random_seed: int = 42,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Generate realistic synthetic transaction data modeled after the UCI Online Retail dataset.
    
    Includes:
    - Normal purchases and cancellations ('C' prefix + negative qty)
    - Skewed order quantities and basket sizes
    - Repeat customers vs one-off buyers
    - Missing customer IDs (~15% representing guest checkout)
    - Temporal seasonality
    """
    rng = np.random.default_rng(random_seed)

    if start_date is None:
        start_dt = datetime(2023, 1, 1, 8, 30)
    else:
        start_dt = datetime.fromisoformat(start_date)

    if end_date is None:
        end_dt = datetime(2023, 12, 31, 18, 0)
    else:
        end_dt = datetime.fromisoformat(end_date)

    total_days = max(1, (end_dt - start_dt).days)

    # Customer base
    num_customers = max(50, num_records // 10)
    customer_ids = [str(12000 + i) for i in range(num_customers)]
    # Pareto weighting for repeat buyers
    cust_weights = rng.pareto(a=1.5, size=num_customers)
    cust_weights /= cust_weights.sum()

    countries, c_probs = zip(*SAMPLE_COUNTRIES)

    records = []
    invoice_counter = 536365

    # Group into invoices/baskets
    approx_baskets = num_records // 3
    for _ in range(approx_baskets):
        invoice_counter += 1
        is_cancel = rng.random() < 0.04
        prefix = "C" if is_cancel else ""
        inv_no = f"{prefix}{invoice_counter}"

        # Assign customer (12% guest checkouts have no CustomerID)
        if rng.random() < 0.12:
            cust_id = None
            country = "United Kingdom"
        else:
            cust_id = rng.choice(customer_ids, p=cust_weights)
            country = rng.choice(countries, p=c_probs)

        # Date with weekday and Q4 peak weighting
        day_offset = rng.integers(0, total_days)
        # Seasonal bump in October - December
        if rng.random() < 0.35 and total_days > 270:
            day_offset = min(total_days - 1, total_days - rng.integers(1, 90))

        hour = rng.integers(8, 19)
        minute = rng.integers(0, 60)
        second = rng.integers(0, 60)
        inv_date = start_dt + timedelta(days=int(day_offset), hours=int(hour), minutes=int(minute), seconds=int(second))

        # Basket items (1 to 6 items per invoice)
        items_count = int(rng.geometric(p=0.45))
        items_count = min(items_count, 6)

        chosen_indices = rng.choice(len(SAMPLE_PRODUCTS), size=items_count, replace=False)

        for p_idx in chosen_indices:
            stock_code, desc, base_price, _ = SAMPLE_PRODUCTS[p_idx]
            # Small random price variance (wholesale discount / surge)
            price_variation = rng.uniform(0.9, 1.1)
            unit_price = round(base_price * price_variation, 2)

            qty = int(rng.choice([1, 2, 3, 4, 6, 12, 24, 48], p=[0.45, 0.22, 0.13, 0.08, 0.06, 0.04, 0.015, 0.005]))
            if is_cancel:
                qty = -qty

            records.append({
                "InvoiceNo": inv_no,
                "StockCode": stock_code,
                "Description": desc,
                "Quantity": qty,
                "InvoiceDate": inv_date.strftime("%Y-%m-%d %H:%M:%S"),
                "UnitPrice": unit_price,
                "CustomerID": cust_id,
                "Country": country,
            })

            if len(records) >= num_records:
                break
        if len(records) >= num_records:
            break

    df = pd.DataFrame(records)
    return df


def load_dataset_from_source(
    source: Union[str, io.BytesIO, io.StringIO, pd.DataFrame]
) -> pd.DataFrame:
    """
    Safely load an e-commerce dataset from a file path, file-like buffer, or DataFrame.
    """
    if isinstance(source, pd.DataFrame):
        return source.copy()

    if isinstance(source, (str, os.PathLike)):
        str_path = str(source)
        if not os.path.exists(str_path):
            raise FileNotFoundError(f"Source file not found at: {str_path}")
        if str_path.endswith((".xlsx", ".xls")):
            return pd.read_excel(str_path)
        return pd.read_csv(str_path, low_memory=False, encoding="utf-8-sig")

    # File-like stream (Streamlit UploadedFile)
    filename = getattr(source, "name", "")
    if str(filename).endswith((".xlsx", ".xls")):
        return pd.read_excel(source)
    try:
        return pd.read_csv(source, low_memory=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        if hasattr(source, "seek"):
            source.seek(0)
        return pd.read_csv(source, low_memory=False, encoding="latin1")
