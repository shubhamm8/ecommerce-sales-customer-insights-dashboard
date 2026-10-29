"""
Page 2: Sales Analytics.
In-depth diagnostic analysis of products, regions, time-series rhythms, and sales volumes.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px
import streamlit as st
from src.sales_analysis import (
    aggregate_sales_time_series,
    analyze_geographic_sales,
    analyze_product_performance,
    analyze_temporal_patterns,
)
from src.visualizations import plot_country_distribution, plot_sales_trend, plot_top_products


st.set_page_config(page_title="Sales Analytics | AI E-Commerce", page_icon="📈", layout="wide")

st.title("📈 Granular Sales & Product Analytics")
st.caption("Detailed transaction breakdown across products, international territories, and temporal purchase cycles.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please visit the homepage to load data.")
    st.stop()

df = st.session_state.cleaned_df

# Tabbed Analysis
tab_products, tab_geo, tab_time = st.tabs(["🏷️ Product Performance", "🌍 Geographic Markets", "⏰ Temporal & Hourly Rhythm"])

with tab_products:
    st.subheader("Catalog Item Diagnostics")
    top_n = st.slider("Select Ranking Depth (Top/Bottom N):", min_value=5, max_value=25, value=10)
    prod_perf = analyze_product_performance(df, top_n=top_n)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(f"#### 🏆 Top {top_n} Revenue Contributors")
        fig_top = plot_top_products(prod_perf["top_revenue"], title=f"Top {top_n} SKUs by Net Revenue", top_n=top_n)
        st.plotly_chart(fig_top, use_container_width=True)

    with col_t2:
        st.markdown(f"#### ⚠️ Bottom {top_n} Trailing SKUs")
        fig_bot = plot_top_products(prod_perf["bottom_revenue"], title=f"Lowest Revenue Active SKUs", top_n=top_n)
        st.plotly_chart(fig_bot, use_container_width=True)

    st.markdown("#### Complete Product Performance Table")
    all_prod = prod_perf["all_products"]
    st.dataframe(all_prod, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Download Product Analytics (CSV)",
        data=all_prod.to_csv(index=False),
        file_name="product_analytics_summary.csv",
        mime="text/csv",
    )

with tab_geo:
    st.subheader("Cross-Border Commercial Distribution")
    geo_df = analyze_geographic_sales(df, top_n=20)

    c_g1, c_g2 = st.columns([1, 1])
    with c_g1:
        fig_pie = plot_country_distribution(geo_df, title="Primary vs Secondary Territory Split")
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_g2:
        st.markdown("#### Territory Sales Ranking")
        st.dataframe(geo_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Download Geographic Breakdown (CSV)",
            data=geo_df.to_csv(index=False),
            file_name="geographic_sales_summary.csv",
            mime="text/csv",
        )

with tab_time:
    st.subheader("Temporal Ordering Cycles")
    temporal = analyze_temporal_patterns(df)
    dow_df = temporal["day_of_week"]
    hod_df = temporal["hour_of_day"]

    c_tm1, c_tm2 = st.columns(2)
    with c_tm1:
        st.markdown("#### Day of the Week Sales Volume")
        fig_dow = px.bar(
            dow_df,
            x="DayOfWeek",
            y="Revenue",
            color="Revenue",
            color_continuous_scale="Teal",
            title="Revenue Distribution by Day of Week",
        )
        fig_dow.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.6)")
        st.plotly_chart(fig_dow, use_container_width=True)

    with c_tm2:
        st.markdown("#### Hourly Checkout Volume (24-Hour Cycle)")
        fig_hod = px.line(
            hod_df,
            x="Hour",
            y="Revenue",
            markers=True,
            title="Hourly Revenue Activity (00:00 to 23:00)",
        )
        fig_hod.update_traces(line=dict(color="#0284c7", width=2.5))
        fig_hod.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.6)")
        st.plotly_chart(fig_hod, use_container_width=True)
