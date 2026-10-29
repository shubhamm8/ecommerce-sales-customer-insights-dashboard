"""
Page 1: Executive Overview.
Comprehensive C-level commercial dashboard with live KPIs, period shifts, and charts.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.metrics import compute_executive_kpis, compute_period_over_period
from src.sales_analysis import aggregate_sales_time_series, analyze_geographic_sales, analyze_product_performance
from src.visualizations import plot_country_distribution, plot_sales_trend, plot_top_products


st.set_page_config(page_title="Executive Overview | AI E-Commerce", page_icon="📊", layout="wide")

st.title("📊 Executive Commercial Overview")
st.caption("Strategic executive summary of financial performance, operational throughput, and global distribution.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please visit the homepage to load benchmark data or upload a file.")
    st.stop()

df = st.session_state.cleaned_df
kpis = compute_executive_kpis(df)
pop = compute_period_over_period(df)

# Top KPI Metric Cards
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    delta_str = f"{pop['delta_pct']:+.1f}%" if pop["status"] == "valid" else None
    st.metric(label="Net Revenue", value=f"${kpis['total_net_revenue']:,.2f}", delta=delta_str)
with col2:
    st.metric(label="Gross Sales", value=f"${kpis['total_gross_revenue']:,.2f}")
with col3:
    st.metric(label="Refunds & Returns", value=f"${kpis['total_refunds']:,.2f}", delta=f"{kpis['cancellation_rate']}% cancel rate", delta_color="inverse")
with col4:
    st.metric(label="Total Invoices", value=f"{kpis['total_orders']:,}")
with col5:
    st.metric(label="Unique Buyers", value=f"{kpis['unique_customers']:,}", delta=f"{kpis['repeat_customer_rate']}% repeat")

st.markdown("---")

# Main Sales Trajectory Area Chart
col_chart, col_side = st.columns([2, 1])

with col_chart:
    st.subheader("📈 Net Sales Trajectory")
    freq_choice = st.radio("Aggregation Interval:", ["Daily", "Weekly", "Monthly"], horizontal=True, index=0)
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    ts_df = aggregate_sales_time_series(df, freq=freq_map[freq_choice])
    fig_trend = plot_sales_trend(ts_df, title=f"{freq_choice} Commercial Sales Velocity")
    st.plotly_chart(fig_trend, use_container_width=True)

with col_side:
    st.subheader("🌍 Geographic Revenue Share")
    geo_df = analyze_geographic_sales(df, top_n=6)
    fig_geo = plot_country_distribution(geo_df, title="Top Markets Distribution")
    st.plotly_chart(fig_geo, use_container_width=True)

st.markdown("---")

# Secondary Charts: Top Products & Performance Highlights
col_p1, col_p2 = st.columns(2)

with col_p1:
    st.subheader("🏆 Flagship Products by Revenue")
    prod_data = analyze_product_performance(df, top_n=8)
    fig_prod = plot_top_products(prod_data["top_revenue"], title="Top 8 Performing SKUs", top_n=8)
    st.plotly_chart(fig_prod, use_container_width=True)

with col_p2:
    st.subheader("📋 Operational & Commercial Scorecard")
    st.dataframe(
        [
            {"Metric": "Active Catalog SKUs", "Value": f"{kpis['total_skus']:,}"},
            {"Metric": "Average Order Value (AOV)", "Value": f"${kpis['average_order_value']:,.2f}"},
            {"Metric": "Total Units Dispatched", "Value": f"{kpis['total_units_sold']:,}"},
            {"Metric": "International Markets Reached", "Value": f"{kpis['total_countries']}"},
            {"Metric": "Invoice Cancellation / Refund Rate", "Value": f"{kpis['cancellation_rate']:.1f}%"},
            {"Metric": "Period-over-Period Sales Shift", "Value": f"{pop['delta_pct']:+.1f}% ({pop['status']})"},
        ],
        use_container_width=True,
        hide_index=True,
    )
    if pop["status"] == "valid":
        st.info(f"💡 Period comparison evaluated across dataset midpoint: **{pop['period_midpoint']}**.")
