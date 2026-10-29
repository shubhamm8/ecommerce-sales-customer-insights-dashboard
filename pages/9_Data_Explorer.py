"""
Page 9: Data Explorer.
Comprehensive dataset auditing, raw vs cleaned data preview, schema validation, and CSV export.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from src.data_cleaning import validate_schema


st.set_page_config(page_title="Data Explorer | AI E-Commerce", page_icon="🔍", layout="wide")

st.title("🔍 Data Engineering & Dataset Explorer")
st.caption("Inspect raw vs cleaned schemas, missing value distributions, cancellation tagging, and export sanitized data.")

if "raw_df" not in st.session_state or st.session_state.raw_df is None:
    st.warning("⚠️ No active dataset loaded. Please visit the homepage to load data.")
    st.stop()

raw_df = st.session_state.raw_df
cleaned_df = st.session_state.cleaned_df
summary = st.session_state.get("cleaning_summary", {})

# Pipeline Summary Metrics
st.subheader("🧹 Cleaning & Preprocessing Summary")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Raw Rows", f"{summary.get('initial_rows', len(raw_df)):,}")
with c2:
    st.metric("Duplicates Removed", f"{summary.get('duplicates_removed', 0):,}")
with c3:
    st.metric("Flagged Cancellations", f"{summary.get('cancellations_count', 0):,}")
with c4:
    st.metric("Cleaned Usable Rows", f"{summary.get('final_rows', len(cleaned_df)):,}")

st.markdown("---")

# Schema & Missing Values Audit
st.subheader("📋 Schema Validation & Data Quality Report")
schema_info = validate_schema(cleaned_df)

col_s1, col_s2 = st.columns(2)

with col_s1:
    st.markdown("#### Column Schema & Types")
    dtype_df = pd.DataFrame({
        "Column": cleaned_df.columns,
        "Data Type": [str(t) for t in cleaned_df.dtypes],
        "Non-Null Count": cleaned_df.count().values,
        "Null Count": cleaned_df.isna().sum().values,
        "Null %": ((cleaned_df.isna().sum().values / len(cleaned_df)) * 100.0).round(2),
    })
    st.dataframe(dtype_df, use_container_width=True, hide_index=True)

with col_s2:
    st.markdown("#### Pipeline Transformation Rules Applied")
    st.markdown(
        """
        1. **Fuzzy Column Normalization:** Automatically standardizes aliases (`invoiceno`, `order_id` → `InvoiceNo`).
        2. **Returns & Cancellation Tagging:** Invoices starting with `'C'` or items with negative quantities flagged with `IsCancelled = True`.
        3. **Zero Price Filtering:** Filtered out negative or zero unit prices (bad records or administrative adjustments).
        4. **Date Parsing:** Standardized ISO date-time conversion with graceful parsing of mixed formats.
        5. **CustomerID Scrubbing:** Preserved null customer IDs as guest checkouts without discarding financial transaction integrity.
        """
    )

st.markdown("---")

# Dataset Previews
tab_clean, tab_raw = st.tabs(["✨ Cleaned Dataset (Active)", "📦 Raw Input Dataset (Unmodified)"])

with tab_clean:
    st.markdown("#### Cleaned Dataset Preview")
    st.dataframe(cleaned_df.head(100), use_container_width=True)
    st.download_button(
        "📥 Export Cleaned Dataset (CSV)",
        data=cleaned_df.to_csv(index=False),
        file_name="cleaned_ecommerce_dataset.csv",
        mime="text/csv",
    )

with tab_raw:
    st.markdown("#### Raw Input Data (First 100 Records)")
    st.dataframe(raw_df.head(100), use_container_width=True)
