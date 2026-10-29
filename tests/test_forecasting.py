"""
Unit tests for chronological time-series sales forecasting and evaluation metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.forecasting import (
    compute_forecast_metrics,
    fit_and_evaluate_forecasting,
    prepare_forecasting_series,
    split_chronological,
)


@pytest.fixture
def synthetic_sales_series():
    dates = pd.date_range("2023-01-01", periods=90, freq="D")
    # Base trend + weekly sine oscillation + noise
    t = np.arange(90)
    sales = 500 + 3.0 * t + 50 * np.sin(2 * np.pi * t / 7)
    return pd.Series(sales, index=dates, name="Sales")


def test_split_chronological_no_data_leakage(synthetic_sales_series):
    train, test = split_chronological(synthetic_sales_series, test_ratio=0.2)

    # Train must strictly precede test in time
    assert train.index.max() < test.index.min()
    assert len(train) + len(test) == len(synthetic_sales_series)
    assert len(test) == 18  # 20% of 90


def test_compute_forecast_metrics():
    y_true = np.array([100.0, 200.0, 300.0])
    y_pred = np.array([110.0, 190.0, 310.0])

    metrics = compute_forecast_metrics(y_true, y_pred)
    # Errors: [10, -10, 10] -> MAE = 10.0, RMSE = 10.0
    assert metrics["mae"] == 10.0
    assert metrics["rmse"] == 10.0
    assert metrics["mape"] > 0


def test_fit_and_evaluate_forecasting(synthetic_sales_series):
    res = fit_and_evaluate_forecasting(synthetic_sales_series, horizon=14, test_ratio=0.2, freq="D")

    assert res["status"] == "success"
    assert "metrics_baseline" in res
    assert "metrics_model" in res
    assert len(res["future_df"]) == 14
    assert "Forecast" in res["future_df"].columns
    assert "Lower_95" in res["future_df"].columns
    assert "Upper_95" in res["future_df"].columns

    # Prediction intervals sanity: lower <= forecast <= upper
    future_df = res["future_df"]
    assert (future_df["Lower_95"] <= future_df["Forecast"]).all()
    assert (future_df["Forecast"] <= future_df["Upper_95"]).all()


def test_fit_and_evaluate_short_series():
    short_series = pd.Series([10.0, 20.0, 15.0], index=pd.date_range("2023-01-01", periods=3))
    res = fit_and_evaluate_forecasting(short_series)
    assert res["status"] == "error"
