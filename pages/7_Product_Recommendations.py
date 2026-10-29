"""
Page 7: Product Recommendations.
Transparent Market Basket Analysis (MBA) using Association Rules (Support, Confidence, and Lift).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.product_recommendations import compute_association_rules, get_product_recommendations
from src.visualizations import plot_association_rules


st.set_page_config(page_title="Product Recommendations | AI E-Commerce", page_icon="🛍️", layout="wide")

st.title("🛍️ Intelligent Product Recommendations (Market Basket Analysis)")
st.caption("Uncovers complementary product affinities and cross-sell rules using transaction co-occurrence mining.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df

# Controls
with st.sidebar:
    st.subheader("⚙️ Association Rule Parameters")
    min_support = st.slider("Minimum Support Threshold:", min_value=0.005, max_value=0.10, value=0.01, step=0.005, format="%.3f")
    min_confidence = st.slider("Minimum Confidence Threshold:", min_value=0.05, max_value=0.80, value=0.10, step=0.05)

# Calculate Rules
with st.spinner("Extracting frequent transaction itemsets and association rules..."):
    rules_df = compute_association_rules(
        df,
        basket_col="InvoiceNo",
        item_col="Description",
        min_support=min_support,
        min_confidence=min_confidence,
    )

# Metric Explanations
with st.expander("ℹ️ How to Interpret Association Rule Metrics"):
    st.markdown(
        r"""
        - **Support \(P(A \cap B)\):** Percentage of all transactions containing both products together.
        - **Confidence \(P(B | A)\):** Likelihood that a customer buys Product B given that they bought Product A.
        - **Lift:** Strength of association.
          - **Lift > 1.0:** Positive affinity (products are bought together significantly more than random chance).
          - **Lift = 1.0:** Independent purchases (no genuine cross-sell relationship).
          - **Lift < 1.0:** Substitute products (buying A decreases chance of buying B).
        """
    )

if rules_df.empty:
    st.info("ℹ️ No association rules met the selected support and confidence thresholds. Try lowering the thresholds in the sidebar.")
    st.stop()

# Rule KPI Summary
st.subheader("📊 Association Rule Mining Findings")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Discovered Association Rules", f"{len(rules_df):,}")
with c2:
    st.metric("Peak Lift Observed", f"{rules_df['Lift'].max():.2f}x")
with c3:
    st.metric("Average Confidence", f"{rules_df['Confidence'].mean():.1%}")

# Rule Scatter Chart
fig_rules = plot_association_rules(rules_df, title="Support vs Confidence Affinity Space (Color = Lift)")
st.plotly_chart(fig_rules, use_container_width=True)

st.markdown("---")

# Product Cross-Sell Finder
st.subheader("🎯 Targeted Product Recommendation Engine")
available_products = sorted(rules_df["Antecedent"].unique().tolist())
selected_product = st.selectbox("Select a Base Product to Find Complementary Cross-Sells:", available_products)

if selected_product:
    recs = get_product_recommendations(selected_product, rules_df, top_n=5)
    if not recs.empty:
        st.markdown(f"#### Recommended Add-Ons for **'{selected_product}'**")
        st.dataframe(recs, use_container_width=True, hide_index=True)
    else:
        st.info("No high-affinity recommendations found for this specific item under current thresholds.")

st.markdown("---")

# Full Rules Table & Export
st.subheader("📋 Top Association Rules Table")
st.dataframe(rules_df.head(50), use_container_width=True, hide_index=True)

st.download_button(
    "📥 Download Complete Association Rules (CSV)",
    data=rules_df.to_csv(index=False),
    file_name="market_basket_association_rules.csv",
    mime="text/csv",
)
