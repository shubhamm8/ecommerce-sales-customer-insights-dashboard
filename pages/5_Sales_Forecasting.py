"""
Page 5: Sales Forecasting.
Machine learning time-series sales forecasting with chronological cross-validation and prediction intervals.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.forecasting import fit_and_evaluate_forecasting, prepare_forecasting_series
from src.visualizations import plot_forecast


st.set_page_config(page_title="Sales Forecasting | AI E-Commerce", page_icon="🔮", layout="wide")

st.title("🔮 Machine Learning Sales Forecasting")
st.caption("Chronologically split time-series forecasting with Holt-Winters Exponential Smoothing, baseline comparison, and prediction intervals.")

if "cleaned_df" not in st.session_state or st.session_state.cleaned_df is None or st.session_state.cleaned_df.empty:
    st.warning("⚠️ No active dataset available. Please load data from the homepage.")
    st.stop()

df = st.session_state.cleaned_df

# Controls
with st.sidebar:
    st.subheader("⚙️ Forecasting Parameters")
    freq_choice = st.selectbox("Aggregation Cadence:", ["Daily (D)", "Weekly (W)"], index=0)
    freq = "D" if "Daily" in freq_choice else "W"

    horizon = st.slider("Forecast Horizon (Periods):", min_value=7, max_value=90, value=30, step=7)
    test_ratio = st.slider("Chronological Test Set Size:", min_value=0.10, max_value=0.35, value=0.20, step=0.05)

# Prepare continuous series
series = prepare_forecasting_series(df, freq=freq)

if len(series) < 14:
    st.error(f"❌ Time series has only {len(series)} chronological periods. At least 14 contiguous periods are required for reliable forecasting.")
    st.stop()

# Run Model
with st.spinner("Fitting time-series forecasting models..."):
    results = fit_and_evaluate_forecasting(series, horizon=horizon, test_ratio=test_ratio, freq=freq)

if results.get("status") == "error":
    st.error(results.get("message"))
    st.stop()

# Model Architecture & Evaluation Scorecard
st.subheader("📊 Model Performance & Backtesting Comparison")
m_base = results["metrics_baseline"]
m_cand = results["metrics_model"]

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Trained Model", results["model_name"])
with c2:
    mae_delta = f"{m_cand['mae'] - m_base['mae']:+.2f} vs Baseline"
    st.metric("Test MAE", f"${m_cand['mae']:,.2f}", delta=mae_delta, delta_color="inverse")
with c3:
    rmse_delta = f"{m_cand['rmse'] - m_base['rmse']:+.2f} vs Baseline"
    st.metric("Test RMSE", f"${m_cand['rmse']:,.2f}", delta=rmse_delta, delta_color="inverse")
with c4:
    st.metric("Test MAPE", f"{m_cand['mape']:.1f}%", help="Mean Absolute Percentage Error on held-out chronological test set")

# Interactive Forecast Chart
st.markdown("---")
fig_forecast = plot_forecast(
    historical_series=results["historical_series"],
    future_df=results["future_df"],
    comparison_df=results["comparison_df"],
    title=f"Sales Trajectory & {horizon}-Period Projected Forecast (with 95% Confidence Cone)",
)
st.plotly_chart(fig_forecast, use_container_width=True)

# Data Tables & Download
col_d1, col_d2 = st.columns(2)

with col_d1:
    st.markdown("#### 📅 Future Forecast Projection")
    st.dataframe(results["future_df"], use_container_width=True, hide_index=True)
    st.download_button(
        "📥 Download Future Forecast (CSV)",
        data=results["future_df"].to_csv(index=False),
        file_name="sales_forecast_projection.csv",
        mime="text/csv",
    )

with col_d2:
    st.markdown("#### 🔬 Out-of-Sample Validation Comparison")
    st.dataframe(results["comparison_df"], use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown(
    r"""
    > **Methodology & Viva Defense Notes:**
    > 1. **No Data Leakage:** Observations are strictly split by chronological time (`iloc[:-test_size]`). Random shuffling in time series leads to severe overfitting.
    > 2. **Baseline Justification:** Any machine learning model must outperform a naive rolling baseline to prove genuine predictive utility.
    > 3. **Uncertainty Bounds:** The 95% confidence cone expands with \(\\sqrt{h}\) over the forecast horizon to reflect compounding forecast variance.
    """
)
