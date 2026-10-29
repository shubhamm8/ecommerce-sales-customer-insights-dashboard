"""
Page 6: Customer Segmentation.
Unsupervised machine learning customer segmentation using RFM feature engineering and Scikit-Learn KMeans clustering.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import plotly.express as px
import streamlit as st
from src.clustering import fit_kmeans_clustering
from src.rfm_analysis import compute_rfm_table
from src.visualizations import plot_rfm_clusters_2d, plot_rfm_clusters_3d


st.set_page_config(page_title="Customer Segmentation | AI E-Commerce", page_icon="🎯", layout="wide")

st.title("🎯 RFM Customer Segmentation (KMeans Clustering)")
st.caption("Data-driven customer clustering combining Recency, Frequency, and Monetary feature engineering with Scikit-Learn KMeans.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df

if "CustomerID" not in df.columns or df["CustomerID"].dropna().empty:
    st.error("❌ The dataset lacks CustomerID fields required for customer behavioral clustering.")
    st.stop()

# RFM Calculation
rfm_df = compute_rfm_table(df)

if len(rfm_df) < 5:
    st.error(f"❌ Found only {len(rfm_df)} identified customers with positive purchases. Clustering requires at least 5 customers.")
    st.stop()

# Controls
with st.sidebar:
    st.subheader("⚙️ Clustering Parameters")
    n_clusters = st.slider("Number of Clusters (k):", min_value=2, max_value=min(6, len(rfm_df) - 1), value=4)
    random_seed = st.number_input("Reproducible Seed (random_state):", value=42, step=1)

# Fit KMeans
with st.spinner("Executing log1p transformations, feature scaling, and KMeans clustering..."):
    results = fit_kmeans_clustering(rfm_df, n_clusters=n_clusters, random_state=random_seed)

if results.get("status") == "error":
    st.error(results.get("message"))
    st.stop()

# Cache in session state
st.session_state.rfm_labeled_df = results["labeled_rfm"]

# Silhouette & Performance Banner
st.subheader("🔬 Cluster Evaluation & Segment Characteristics")
sil = results["silhouette"]

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Optimal Silhouette Score", f"{sil:.4f}", help="Ranges from -1 to +1. Values > 0.35 indicate solid cluster separation.")
with c2:
    st.metric("Total Segmented Customers", f"{len(rfm_df):,}")
with c3:
    st.metric("Cluster Count (k)", n_clusters)

# Cluster Summary Table
st.markdown("#### Segment Profile Summary")
st.dataframe(results["cluster_summary"], use_container_width=True, hide_index=True)

st.markdown("---")

# Visualizations
tab_3d, tab_2d, tab_eval = st.tabs(["🌐 3D Feature Space", "🗺️ 2D Segmentation Map", "📐 Elbow & Silhouette Curve"])

with tab_3d:
    st.subheader("3D Interactive RFM Feature Space")
    fig_3d = plot_rfm_clusters_3d(results["labeled_rfm"], title="Customer Positioning in 3D RFM Space")
    st.plotly_chart(fig_3d, use_container_width=True)

with tab_2d:
    st.subheader("2D Recency vs Spend Map (Bubble Size = Order Frequency)")
    fig_2d = plot_rfm_clusters_2d(results["labeled_rfm"], title="Recency vs Monetary Spend")
    st.plotly_chart(fig_2d, use_container_width=True)

with tab_eval:
    st.subheader("Elbow Inertia and Silhouette Analysis across k")
    eval_df = results["evaluation_df"]
    if not eval_df.empty:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            fig_inertia = px.line(eval_df, x="k", y="inertia", markers=True, title="Elbow Method (Inertia vs k)")
            fig_inertia.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.6)")
            st.plotly_chart(fig_inertia, use_container_width=True)
        with col_e2:
            fig_sil = px.line(eval_df, x="k", y="silhouette", markers=True, title="Silhouette Score vs k")
            fig_sil.update_traces(line=dict(color="#0d9488"))
            fig_sil.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(248, 250, 252, 0.6)")
            st.plotly_chart(fig_sil, use_container_width=True)

st.markdown("---")

# Download Labeled Data
st.subheader("📥 Export Customer Segment Assignments")
st.dataframe(results["labeled_rfm"].head(20), use_container_width=True, hide_index=True)

st.download_button(
    "📥 Download Customer Segments (CSV)",
    data=results["labeled_rfm"].to_csv(index=False),
    file_name="customer_kmeans_segments.csv",
    mime="text/csv",
)
