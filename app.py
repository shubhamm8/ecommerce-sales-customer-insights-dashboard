"""
AI-Powered E-Commerce Sales and Customer Insights Dashboard
Main Application Entry Point.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.audit_log import initialize_audit_log, log_event
from src.data_cleaning import clean_ecommerce_data, validate_schema
from src.data_loader import generate_synthetic_ecommerce_data, load_dataset_from_source
from src.local_llm import check_ollama_status
from src.metrics import compute_executive_kpis


# Streamlit Page Configuration
st.set_page_config(
    page_title="AI E-Commerce Sales & Customer Insights",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern typography and cards
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .metric-subtitle {
        font-size: 0.78rem;
        color: #94a3b8;
    }
    .badge-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-success { background-color: #dcfce7; color: #15803d; }
    .badge-warning { background-color: #fef3c7; color: #b45309; }
    .badge-info { background-color: #e0f2fe; color: #0369a1; }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state():
    """Ensure persistent session state variables exist."""
    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None
    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = None
    if "cleaning_summary" not in st.session_state:
        st.session_state.cleaning_summary = None
    if "dataset_name" not in st.session_state:
        st.session_state.dataset_name = "Sample UCI E-Commerce Data"
    if "is_sample" not in st.session_state:
        st.session_state.is_sample = True
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_start" not in st.session_state:
        st.session_state.session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    initialize_audit_log()


initialize_session_state()


def load_default_data():
    """Load built-in synthetic benchmark dataset."""
    sample_path = PROJECT_ROOT / "data" / "sample_ecommerce.csv"
    if sample_path.exists():
        raw = load_dataset_from_source(sample_path)
        log_event("DATA_LOAD", f"Loaded dataset from file: {sample_path.name} ({len(raw):,} rows)")
    else:
        raw = generate_synthetic_ecommerce_data(num_records=2500, random_seed=42)
        log_event("DATA_LOAD", "Generated synthetic benchmark dataset (2,500 records, seed=42)")
    cleaned, summary = clean_ecommerce_data(raw)
    st.session_state.raw_df = raw
    st.session_state.cleaned_df = cleaned
    st.session_state.cleaning_summary = summary
    st.session_state.dataset_name = "Sample UCI Online Retail (Benchmark)"
    st.session_state.is_sample = True
    log_event("DATA_CLEAN", f"Data cleaning complete: {len(cleaned):,} valid rows retained from {len(raw):,} raw rows")


# Automatically load sample dataset on initial load
if st.session_state.cleaned_df is None:
    load_default_data()


# ---------------- SIDEBAR NAVIGATION & DATA MANAGEMENT ----------------
with st.sidebar:
    st.title("🛒 AI E-Commerce Insights")
    st.caption("Final-Year Data Science & ML Capstone")

    st.markdown("---")
    st.subheader("📁 Data Source")

    source_option = st.radio(
        "Select Dataset:",
        ["Built-In Benchmark Sample", "Upload Custom CSV / Excel"],
        index=0 if st.session_state.is_sample else 1,
    )

    if source_option == "Built-In Benchmark Sample":
        if not st.session_state.is_sample or st.session_state.cleaned_df is None:
            if st.button("🔄 Reset to Benchmark Data"):
                load_default_data()
                st.success("Loaded benchmark dataset.")
                st.rerun()
    else:
        uploaded_file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx", "xls"])
        if uploaded_file is not None:
            try:
                raw_up = load_dataset_from_source(uploaded_file)
                cleaned_up, summary_up = clean_ecommerce_data(raw_up)
                st.session_state.raw_df = raw_up
                st.session_state.cleaned_df = cleaned_up
                st.session_state.cleaning_summary = summary_up
                st.session_state.dataset_name = uploaded_file.name
                st.session_state.is_sample = False
                st.success(f"Loaded '{uploaded_file.name}' ({len(cleaned_up):,} valid records)")
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")

    st.markdown("---")
    st.subheader("🤖 Local AI Engine")
    ollama_info = check_ollama_status()

    if ollama_info["available"]:
        st.markdown(
            f'<span class="badge-pill badge-success">● Ollama Online</span> ({len(ollama_info["models"])} models)',
            unsafe_allow_html=True,
        )
        st.caption(f"Host: `{ollama_info['host']}`")
    else:
        st.markdown(
            '<span class="badge-pill badge-warning">○ Deterministic Assistant Active</span>',
            unsafe_allow_html=True,
        )
        st.caption("Local Ollama daemon offline. Running deterministic rule-based assistant.")

    st.markdown("---")
    if st.session_state.cleaned_df is not None:
        df_curr = st.session_state.cleaned_df
        min_date = df_curr["InvoiceDate"].min().date() if "InvoiceDate" in df_curr.columns else datetime.now().date()
        max_date = df_curr["InvoiceDate"].max().date() if "InvoiceDate" in df_curr.columns else datetime.now().date()
        st.caption(f"📊 **Active Data:** {len(df_curr):,} rows")
        st.caption(f"📅 **Date Range:** {min_date} to {max_date}")

        if st.session_state.is_sample:
            st.info("ℹ️ Using synthetic sample data modeled after UCI Online Retail.")


# ---------------- MAIN LANDING PAGE ----------------
st.title("AI-Powered E-Commerce Sales and Customer Insights Dashboard")
st.markdown(
    """
    Welcome to the **comprehensive end-to-end commercial intelligence platform**.
    This application integrates **statistical data engineering**, **machine learning forecasting**, 
    **KMeans customer segmentation**, **market basket analysis**, **anomaly detection**, and a **privacy-preserving local AI assistant**.
    """
)

df = st.session_state.cleaned_df

if df is not None and not df.empty:
    kpis = compute_executive_kpis(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Net Sales Revenue</div>
                <div class="metric-value">${kpis['total_net_revenue']:,.2f}</div>
                <div class="metric-subtitle">Gross: ${kpis['total_gross_revenue']:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Completed Orders</div>
                <div class="metric-value">{kpis['total_orders']:,}</div>
                <div class="metric-subtitle">Cancellation Rate: {kpis['cancellation_rate']}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Unique Customers</div>
                <div class="metric-value">{kpis['unique_customers']:,}</div>
                <div class="metric-subtitle">Repeat Rate: {kpis['repeat_customer_rate']}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Average Order Value</div>
                <div class="metric-value">${kpis['average_order_value']:,.2f}</div>
                <div class="metric-subtitle">Units Sold: {kpis['total_units_sold']:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("### 🧭 Platform Modules Navigation")

nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    st.markdown("#### 📈 Business Intelligence")
    st.markdown("1. **Executive Overview**: High-level KPIs, executive trajectory, and performance breakdown.")
    st.markdown("2. **Sales Analytics**: Deep-dive product rankings, geographic demand, and temporal distributions.")
    st.markdown("3. **Customer Insights**: Lifetime spend, Pareto 80/20 concentration, and customer frequency.")
    st.markdown("4. **Data Explorer**: Raw vs cleaned validation, schema audits, and clean CSV export.")

with nav_col2:
    st.markdown("#### 🤖 Machine Learning & AI")
    st.markdown("5. **Sales Forecasting**: Chronological train/test time-series modeling with prediction intervals.")
    st.markdown("6. **Customer Segmentation**: RFM feature engineering and Scikit-Learn KMeans clustering.")
    st.markdown("7. **Product Recommendations**: Market Basket Analysis (Support, Confidence, and Lift rules).")
    st.markdown("8. **Anomaly Detection**: Statistical rolling variance, MAD, and Isolation Forest.")

with nav_col3:
    st.markdown("#### 💡 Decision Support")
    st.markdown("9. **AI Sales Assistant**: Local privacy-preserving LLM assistant with deterministic fallback.")
    st.markdown("10. **Business Insights & Recommendations**: 7-dimension automated strategic action generator.")

st.markdown("---")
st.markdown(
    """
    > **Academic Viva & Reproducibility Note:**
    > All numbers, tables, forecasts, and segment allocations are dynamically derived from the active dataset. 
    > Machine learning random seeds are fixed (`random_state=42`) to guarantee reproducible scientific evaluation.
    """
)
