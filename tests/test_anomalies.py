"""
Unit tests for sales anomaly detection algorithms.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.anomaly_detection import (
    detect_anomalies_isolation_forest,
    detect_anomalies_robust_mad,
    detect_anomalies_rolling,
    run_anomaly_detection,
)


@pytest.fixture
def series_with_known_anomaly():
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    rng = np.random.default_rng(42)
    values = rng.normal(loc=100.0, scale=5.0, size=30)
    # Inject an intentional extreme spike at day 15 (e.g. Black Friday flash sale)
    values[15] = 450.0
    return pd.Series(values, index=dates, name="Sales")


def test_detect_anomalies_rolling(series_with_known_anomaly):
    df_res = detect_anomalies_rolling(series_with_known_anomaly, window=7, threshold=2.5)
    assert not df_res.empty
    # Day 15 should be identified as anomaly
    anom_dates = df_res[df_res["IsAnomaly"]]["Date"].dt.strftime("%Y-%m-%d").tolist()
    assert "2023-01-16" in anom_dates or "2023-01-15" in anom_dates


def test_detect_anomalies_robust_mad(series_with_known_anomaly):
    df_res = detect_anomalies_robust_mad(series_with_known_anomaly, threshold=3.0)
    assert not df_res.empty
    anom_rows = df_res[df_res["IsAnomaly"]]
    assert len(anom_rows) >= 1
    # Check max score is at the injected spike
    top_anom = df_res.sort_values(by="Score", ascending=False).iloc[0]
    assert top_anom["Value"] == 450.0


def test_detect_anomalies_isolation_forest(series_with_known_anomaly):
    df_res = detect_anomalies_isolation_forest(series_with_known_anomaly, contamination=0.05)
    assert not df_res.empty
    assert "IsAnomaly" in df_res.columns
    assert "Score" in df_res.columns


def test_run_anomaly_detection_wrapper(series_with_known_anomaly):
    res = run_anomaly_detection(series_with_known_anomaly, method="rolling", sensitivity=2.5)
    assert res["status"] == "success"
    assert res["anomaly_count"] >= 1
    assert "df_anomalies" in res
