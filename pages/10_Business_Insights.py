"""
Page 10: Business Insights and Recommendations.
Automated strategic insights generator providing evidence-backed business recommendations.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from src.clustering import fit_kmeans_clustering
from src.recommendations import generate_business_insights
from src.rfm_analysis import compute_rfm_table


st.set_page_config(page_title="Business Insights | AI E-Commerce", page_icon="💡", layout="wide")

st.title("💡 Strategic Business Insights & Action Plan")
st.caption("Automated decision-intelligence engine delivering evidence-grounded strategic recommendations across 7 commercial dimensions.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df

# Check or generate RFM labeled data
rfm_labeled = st.session_state.get("rfm_labeled_df", None)
if rfm_labeled is None and "CustomerID" in df.columns and not df["CustomerID"].dropna().empty:
    rfm_table = compute_rfm_table(df)
    if len(rfm_table) >= 4:
        km_res = fit_kmeans_clustering(rfm_table, n_clusters=4)
        if km_res.get("status") == "success":
            rfm_labeled = km_res["labeled_rfm"]
            st.session_state.rfm_labeled_df = rfm_labeled

# Retrieve cached anomaly findings if available
anomaly_summary = st.session_state.get("anomaly_cache", None)

# Generate insights
insights = generate_business_insights(df, rfm_labeled_df=rfm_labeled, anomaly_summary=anomaly_summary)

if not insights:
    st.info("No actionable findings could be derived from the current dataset.")
    st.stop()

st.subheader(f"🎯 Derived Strategic Insights ({len(insights)} Actionable Findings)")

# Filter by category
categories = ["All Categories"] + sorted(list(set(i["category"] for i in insights)))
selected_cat = st.selectbox("Filter by Focus Area:", categories)

filtered_insights = insights if selected_cat == "All Categories" else [i for i in insights if i["category"] == selected_cat]

for idx, item in enumerate(filtered_insights, 1):
    tag_color = "#0369a1" if "Revenue" in item["category"] or "Growth" in item.get("tag", "") else ("#b45309" if "Risk" in item.get("tag", "") else "#0d9488")
    bg_color = "#e0f2fe" if "Revenue" in item["category"] or "Growth" in item.get("tag", "") else ("#fef3c7" if "Risk" in item.get("tag", "") else "#ccfbf1")

    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px 22px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #64748b;">
                        {item['category']}
                    </span>
                    <span style="background-color: {bg_color}; color: {tag_color}; padding: 3px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">
                        {item.get('tag', 'Strategic')}
                    </span>
                </div>
                <h4 style="margin: 0 0 10px 0; color: #0f172a;">{item['title']}</h4>
                <p style="margin: 4px 0; color: #334155;"><strong>📊 Supporting Evidence:</strong> {item['supporting_metric']} (<em>{item['comparison']}</em>)</p>
                <p style="margin: 4px 0; color: #334155;"><strong>🔍 Why It Matters:</strong> {item['why_it_matters']}</p>
                <div style="margin-top: 10px; padding: 10px 14px; background-color: #f8fafc; border-left: 3px solid #0284c7; border-radius: 4px;">
                    <strong style="color: #0284c7;">🎯 Recommended Business Action:</strong> {item['recommended_action']}
                </div>
                <div style="margin-top: 8px; font-size: 0.75rem; color: #94a3b8;">
                    Confidence: <strong>{item['confidence']}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# Downloadable Executive Action Plan
st.subheader("📥 Export Executive Decision Report")
insights_df = pd.DataFrame(insights)
st.download_button(
    "📥 Download Strategic Action Plan (CSV)",
    data=insights_df.to_csv(index=False),
    file_name="executive_strategic_action_plan.csv",
    mime="text/csv",
)
