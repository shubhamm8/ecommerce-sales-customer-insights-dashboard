"""
Page 3: Customer Insights.
Evaluates customer lifetime spend, Pareto revenue concentration, and retention tenure.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px
import streamlit as st
from src.customer_analysis import analyze_pareto_concentration, compute_customer_summary


st.set_page_config(page_title="Customer Insights | AI E-Commerce", page_icon="👥", layout="wide")

st.title("👥 Customer Cohort & Concentration Insights")
st.caption("Deep behavioral intelligence, lifetime value calculations, and Pareto concentration analysis.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df

if "CustomerID" not in df.columns or df["CustomerID"].dropna().empty:
    st.error("❌ The active dataset contains no CustomerID values. Customer-level metrics cannot be computed.")
    st.stop()

cust_summary = compute_customer_summary(df)
pareto = analyze_pareto_concentration(cust_summary)

# Concentration KPI Banner
st.subheader("⚖️ Pareto Revenue Concentration (80/20 Analysis)")
cp1, cp2, cp3, cp4 = st.columns(4)
with cp1:
    st.metric("Top 20% Customers Revenue Share", f"{pareto['top_20_pct_revenue_share']:.1f}%")
with cp2:
    st.metric("Top 10% Customers Revenue Share", f"{pareto['top_10_pct_revenue_share']:.1f}%")
with cp3:
    st.metric("Top 5% Elite Spenders Share", f"{pareto['top_5_pct_revenue_share']:.1f}%")
with cp4:
    st.metric("Gini Inequality Index", f"{pareto['gini_coefficient']:.3f}", help="0 = completely equal spend, 1 = extreme concentration in few buyers")

st.markdown("---")

col_l, col_r = st.columns([1, 1])

with col_l:
    st.subheader("💰 Customer Spend Distribution (Log Scale)")
    fig_hist = px.histogram(
        cust_summary[cust_summary["TotalSpend"] > 0],
        x="TotalSpend",
        nbins=40,
        log_x=True,
        title="Distribution of Customer Total Spend ($)",
        color_discrete_sequence=["#0284c7"],
    )
    fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.6)")
    st.plotly_chart(fig_hist, use_container_width=True)

with col_r:
    st.subheader("📦 Order Frequency Distribution")
    fig_freq = px.histogram(
        cust_summary,
        x="OrderCount",
        nbins=25,
        title="Distinct Invoices per Customer",
        color_discrete_sequence=["#0d9488"],
    )
    fig_freq.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.6)")
    st.plotly_chart(fig_freq, use_container_width=True)

st.markdown("---")

# Customer Directory
st.subheader("📋 Customer Directory & Leaderboard")
search_term = st.text_input("🔍 Search Customer by ID or Country:", "")

filtered_cust = cust_summary
if search_term:
    mask = (
        filtered_cust["CustomerID"].astype(str).str.contains(search_term, case=False, na=False)
        | filtered_cust["Country"].astype(str).str.contains(search_term, case=False, na=False)
    )
    filtered_cust = filtered_cust[mask]

st.dataframe(filtered_cust, use_container_width=True, hide_index=True)

st.download_button(
    "📥 Download Customer Summary (CSV)",
    data=cust_summary.to_csv(index=False),
    file_name="customer_insights_summary.csv",
    mime="text/csv",
)
