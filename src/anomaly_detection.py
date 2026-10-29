"""
Sales Anomaly Detection Engine.

Implements three statistical and machine-learning methodologies:
1. Rolling Statistics (Mean +/- k * Rolling Std)
2. Robust Z-Score (Median and Median Absolute Deviation - MAD)
3. Isolation Forest (Unsupervised tree-based anomaly isolation)

Ensures transparency and avoids false accusations by characterizing deviations
as 'potential anomalies' requiring investigation rather than confirmed fraud.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies_rolling(
    series: pd.Series,
    window: int = 7,
    threshold: float = 2.5,
) -> pd.DataFrame:
    """
    Detect spikes and drops using rolling window baseline (excluding current point to prevent masking).
    """
    if len(series) < window:
        return pd.DataFrame(columns=["Date", "Value", "Baseline", "Deviation", "Score", "IsAnomaly", "Type"])

    # Compute baseline from previous observations so an extreme outlier doesn't inflate std and mask itself
    prior_series = series.shift(1)
    overall_mean = float(series.mean())
    overall_std = float(series.std()) if series.std() > 0 else 1.0

    rolling_mean = prior_series.rolling(window=window, min_periods=2).mean().fillna(overall_mean)
    rolling_std = prior_series.rolling(window=window, min_periods=2).std().fillna(overall_std)

    # Avoid zero division
    rolling_std = np.where(rolling_std < 1e-4, overall_std, rolling_std)

    z_scores = (series - rolling_mean) / rolling_std
    is_anomaly = np.abs(z_scores) >= threshold

    results = []
    for idx, dt in enumerate(series.index):
        val = float(series.iloc[idx])
        base = float(rolling_mean.iloc[idx]) if not np.isnan(rolling_mean.iloc[idx]) else val
        z = float(z_scores.iloc[idx]) if not np.isnan(z_scores.iloc[idx]) else 0.0
        anom = bool(is_anomaly.iloc[idx])

        a_type = "Normal"
        if anom:
            a_type = "High Sales Spike" if z > 0 else "Low Sales Drop"

        results.append({
            "Date": dt,
            "Value": round(val, 2),
            "Baseline": round(base, 2),
            "Deviation": round(val - base, 2),
            "Score": round(abs(z), 2),
            "IsAnomaly": anom,
            "Type": a_type,
        })

    return pd.DataFrame(results)


def detect_anomalies_robust_mad(
    series: pd.Series,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """
    Detect anomalies using robust Median and Median Absolute Deviation (MAD).
    Insensitive to extreme outliers compared to standard mean/variance.
    """
    if len(series) < 5:
        return pd.DataFrame(columns=["Date", "Value", "Baseline", "Deviation", "Score", "IsAnomaly", "Type"])

    median = float(series.median())
    abs_deviations = np.abs(series.values - median)
    mad = float(np.median(abs_deviations))

    # Consistency constant for normal distribution: 1.4826
    mad_scaled = 1.4826 * mad
    if mad_scaled < 1e-4:
        mad_scaled = float(series.std()) if series.std() > 0 else 1.0

    robust_scores = (series.values - median) / mad_scaled
    is_anomaly = np.abs(robust_scores) >= threshold

    results = []
    for idx, dt in enumerate(series.index):
        val = float(series.iloc[idx])
        score = float(robust_scores[idx])
        anom = bool(is_anomaly[idx])
        a_type = "Normal"
        if anom:
            a_type = "High Sales Spike" if score > 0 else "Low Sales Drop"

        results.append({
            "Date": dt,
            "Value": round(val, 2),
            "Baseline": round(median, 2),
            "Deviation": round(val - median, 2),
            "Score": round(abs(score), 2),
            "IsAnomaly": anom,
            "Type": a_type,
        })

    return pd.DataFrame(results)


def detect_anomalies_isolation_forest(
    series: pd.Series,
    contamination: float = 0.03,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Unsupervised multi-feature anomaly detection via Scikit-Learn IsolationForest.
    Features: [Value, DayOfWeek, RollingDiff]
    """
    if len(series) < 14:
        return pd.DataFrame(columns=["Date", "Value", "Baseline", "Deviation", "Score", "IsAnomaly", "Type"])

    df_features = pd.DataFrame({
        "Value": series.values,
        "DayOfWeek": [d.day_of_week for d in series.index],
        "Diff": series.diff().fillna(0).values,
    })

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
    )
    preds = model.fit_predict(df_features)  # -1 for anomalies, 1 for normal
    raw_scores = -model.score_samples(df_features)  # higher = more anomalous

    median_val = float(series.median())
    results = []
    for idx, dt in enumerate(series.index):
        val = float(series.iloc[idx])
        is_anom = (preds[idx] == -1)
        score = float(raw_scores[idx])
        dev = val - median_val

        a_type = "Normal"
        if is_anom:
            a_type = "High Sales Spike" if dev > 0 else "Low Sales Drop"

        results.append({
            "Date": dt,
            "Value": round(val, 2),
            "Baseline": round(median_val, 2),
            "Deviation": round(dev, 2),
            "Score": round(score, 3),
            "IsAnomaly": is_anom,
            "Type": a_type,
        })

    return pd.DataFrame(results)


def run_anomaly_detection(
    time_series: pd.Series,
    method: Literal["rolling", "robust_mad", "isolation_forest"] = "rolling",
    sensitivity: float = 2.5,
) -> Dict[str, Any]:
    """
    Execute selected anomaly detection algorithm with comprehensive reporting.
    """
    if time_series.empty or len(time_series) < 5:
        return {
            "status": "error",
            "message": "Time series has insufficient points for statistical anomaly detection.",
            "df_anomalies": pd.DataFrame(),
            "anomaly_count": 0,
            "anomaly_rate": 0.0,
        }

    if method == "robust_mad":
        df_res = detect_anomalies_robust_mad(time_series, threshold=sensitivity)
        desc = "Robust Z-Score using Median Absolute Deviation (MAD)"
    elif method == "isolation_forest":
        contam = min(0.15, max(0.01, 1.0 / sensitivity if sensitivity > 0 else 0.05))
        df_res = detect_anomalies_isolation_forest(time_series, contamination=contam)
        desc = "Unsupervised Isolation Forest Machine Learning"
    else:
        df_res = detect_anomalies_rolling(time_series, window=7, threshold=sensitivity)
        desc = "Rolling Window (7-day) Mean & Variance Envelope"

    anom_rows = df_res[df_res["IsAnomaly"]].copy()
    count = len(anom_rows)
    rate = (count / len(df_res) * 100.0) if len(df_res) > 0 else 0.0

    return {
        "status": "success",
        "method": method,
        "description": desc,
        "df_full": df_res,
        "df_anomalies": anom_rows.sort_values(by="Score", ascending=False),
        "anomaly_count": count,
        "anomaly_rate": round(rate, 2),
    }
