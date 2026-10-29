"""
Page 8: Anomaly Detection.
Statistical and unsupervised machine learning detection of potential sales spikes and drops.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.anomaly_detection import run_anomaly_detection
from src.forecasting import prepare_forecasting_series
from src.visualizations import plot_anomalies


st.set_page_config(page_title="Anomaly Detection | AI E-Commerce", page_icon="🚨", layout="wide")

st.title("🚨 Commercial Sales Anomaly Detection")
st.caption("Identify statistical deviations, sales surges, and unexpected operational drops using rolling statistics, robust MAD, or Isolation Forests.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df
daily_series = prepare_forecasting_series(df, freq="D")

if len(daily_series) < 7:
    st.error("❌ The dataset has fewer than 7 days of historical timeline. Anomaly detection requires at least 7 continuous days.")
    st.stop()

# Controls
with st.sidebar:
    st.subheader("⚙️ Anomaly Detection Setup")
    method_label = st.selectbox(
        "Detection Algorithm:",
        [
            "Rolling Window (7-Day Envelope)",
            "Robust Z-Score (Median Absolute Deviation)",
            "Scikit-Learn Isolation Forest",
        ],
        index=0,
    )

    method_map = {
        "Rolling Window (7-Day Envelope)": "rolling",
        "Robust Z-Score (Median Absolute Deviation)": "robust_mad",
        "Scikit-Learn Isolation Forest": "isolation_forest",
    }
    method = method_map[method_label]

    sensitivity = st.slider(
        "Sensitivity / Threshold Multiplier:",
        min_value=1.5,
        max_value=4.0,
        value=2.5,
        step=0.25,
        help="Higher values detect only extreme outliers. Lower values flag milder variances.",
    )

# Run Anomaly Detection
with st.spinner("Analyzing timeline for statistical deviations..."):
    results = run_anomaly_detection(daily_series, method=method, sensitivity=sensitivity)

if results.get("status") == "error":
    st.error(results.get("message"))
    st.stop()

# Cache in session state for business insights engine
st.session_state.anomaly_cache = results

# Metrics Banner
st.subheader("📊 Detection Diagnostics")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Method Applied", results["description"])
with c2:
    st.metric("Flagged Potential Anomalies", f"{results['anomaly_count']} days")
with c3:
    st.metric("Anomaly Rate", f"{results['anomaly_rate']:.1f}%")

# Interactive Timeline Chart
fig_anom = plot_anomalies(results["df_full"], title=f"Timeline Deviations: {results['description']}")
st.plotly_chart(fig_anom, use_container_width=True)

st.markdown("---")

# Anomaly Investigation Table
st.subheader("📋 Flagged Deviation Log")
st.caption("Note: All flagged observations are categorized as 'potential anomalies' requiring commercial verification (e.g. promotional campaign or stockout) rather than confirmed fraud.")

df_anoms = results["df_anomalies"]
if not df_anoms.empty:
    st.dataframe(df_anoms, use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Download Anomaly Report (CSV)",
        data=df_anoms.to_csv(index=False),
        file_name="detected_sales_anomalies.csv",
        mime="text/csv",
    )
else:
    st.success("✅ No statistical anomalies detected under the current sensitivity threshold.")

st.markdown("---")
with st.expander("ℹ️ Scientific Methodology & Comparison of Techniques"):
    st.markdown(
        r"""
        - **Rolling Window Envelope:** Uses moving average \(\mu_{7}\) and rolling standard deviation \(\sigma_{7}\). Ideal for detecting local day-over-day spikes while adapting to gradual secular trends.
        - **Robust Median Absolute Deviation (MAD):** Uses \(\text{Median}\) and \(\text{MAD} = \text{Median}(|X - \text{Median}|)\). Significantly more resistant to extreme historical outliers than standard z-scores.
        - **Isolation Forest:** Tree-based unsupervised algorithm that isolates anomalous observations by randomly partitioning feature dimensions (`Value`, `DayOfWeek`, `DailyDiff`).
        """
    )
