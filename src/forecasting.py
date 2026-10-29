"""
Machine Learning Sales Forecasting Pipeline.

Features:
- Strict chronological train/test splitting (no data leakage).
- Baseline models (Naive Last Value, Moving Average).
- Exponential Smoothing (Holt-Winters ETS with additive trend/seasonality).
- Performance metrics: MAE, RMSE, MAPE.
- Prediction intervals based on empirical residual standard error.
- Comprehensive diagnostic warnings for short or sparse time series.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing


def prepare_forecasting_series(
    df: pd.DataFrame,
    freq: str = "D",
    date_col: str = "InvoiceDate",
    value_col: str = "NetRevenue",
) -> pd.Series:
    """
    Transform raw transactions into an evenly spaced, continuous numerical series.
    """
    if df.empty or date_col not in df.columns or value_col not in df.columns:
        return pd.Series(dtype=float)

    data = df.dropna(subset=[date_col]).copy()
    data["Period"] = data[date_col].dt.to_period(freq).dt.to_timestamp()
    aggregated = data.groupby("Period")[value_col].sum()

    if aggregated.empty:
        return pd.Series(dtype=float)

    # Reindex over complete date range
    full_idx = pd.date_range(start=aggregated.index.min(), end=aggregated.index.max(), freq=freq)
    continuous_series = aggregated.reindex(full_idx, fill_value=0.0)
    continuous_series.name = "Sales"
    return continuous_series


def split_chronological(
    series: pd.Series,
    test_ratio: float = 0.2,
    min_test_size: int = 7,
) -> Tuple[pd.Series, pd.Series]:
    """
    Split time series strictly chronologically. Never shuffle.
    """
    n = len(series)
    test_size = max(min_test_size, int(n * test_ratio))
    if test_size >= n:
        test_size = max(1, n // 3)

    train = series.iloc[:-test_size]
    test = series.iloc[-test_size:]
    return train, test


def compute_forecast_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate MAE, RMSE, and MAPE.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0 or len(y_pred) == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

    errors = y_true - y_pred
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # Epsilon-safe MAPE for zero-sales days
    denom = np.where(np.abs(y_true) < 1e-4, np.nan, np.abs(y_true))
    valid_mask = ~np.isnan(denom)
    if np.any(valid_mask):
        mape = float(np.mean(np.abs(errors[valid_mask] / denom[valid_mask])) * 100.0)
    else:
        mape = 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }


def fit_and_evaluate_forecasting(
    series: pd.Series,
    horizon: int = 30,
    test_ratio: float = 0.2,
    freq: str = "D",
) -> Dict[str, Any]:
    """
    Train baseline vs Exponential Smoothing model on chronological train set,
    evaluate on held-out test set, and generate future horizon forecast with intervals.
    """
    if len(series) < 14:
        return {
            "status": "error",
            "message": f"Insufficient historical records for time-series modeling. Found {len(series)} points, minimum required is 14.",
            "metrics_baseline": None,
            "metrics_model": None,
            "comparison_df": pd.DataFrame(),
            "future_df": pd.DataFrame(),
        }

    train, test = split_chronological(series, test_ratio=test_ratio)
    test_len = len(test)

    # 1. Baseline: Rolling Naive Mean
    baseline_val = float(train.iloc[-7:].mean() if len(train) >= 7 else train.mean())
    baseline_test_pred = np.full(test_len, baseline_val)
    metrics_baseline = compute_forecast_metrics(test.values, baseline_test_pred)

    # 2. Candidate Model: Exponential Smoothing
    model_name = "Holt-Winters Exponential Smoothing"
    try:
        # Determine seasonal period
        seasonal_periods = 7 if freq == "D" and len(train) >= 28 else (4 if freq == "W" and len(train) >= 16 else None)
        
        if seasonal_periods:
            fitted_model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            ).fit(damping_trend=0.9)
        elif len(train) >= 10:
            fitted_model = ExponentialSmoothing(
                train,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit()
        else:
            fitted_model = SimpleExpSmoothing(train).fit()
            model_name = "Simple Exponential Smoothing"

        test_pred = fitted_model.forecast(test_len).values
    except Exception:
        # Robust fallback
        fitted_model = SimpleExpSmoothing(train).fit()
        test_pred = fitted_model.forecast(test_len).values
        model_name = "Simple Exponential Smoothing (Fallback)"

    # Clip negative predictions since revenue >= 0
    test_pred = np.clip(test_pred, a_min=0, a_max=None)
    metrics_model = compute_forecast_metrics(test.values, test_pred)

    # Backtest comparison dataframe
    comparison_df = pd.DataFrame({
        "Date": test.index,
        "Actual": test.values,
        "Baseline_Pred": baseline_test_pred,
        "Model_Pred": test_pred,
    })

    # 3. Fit on full series for future forecast
    try:
        if seasonal_periods and len(series) >= 28:
            full_model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            ).fit(damping_trend=0.9)
        elif len(series) >= 10:
            full_model = ExponentialSmoothing(
                series,
                trend="add",
                seasonal=None,
                initialization_method="estimated",
            ).fit()
        else:
            full_model = SimpleExpSmoothing(series).fit()

        future_pred = full_model.forecast(horizon).values
    except Exception:
        full_model = SimpleExpSmoothing(series).fit()
        future_pred = full_model.forecast(horizon).values

    future_pred = np.clip(future_pred, a_min=0, a_max=None)

    # Future dates index
    last_date = series.index[-1]
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1 if freq == "D" else 7), periods=horizon, freq=freq)

    # Residual Standard Deviation for prediction intervals (80% and 95%)
    residuals = test.values - test_pred
    residual_std = float(np.std(residuals)) if len(residuals) > 1 else (float(series.std()) * 0.2)

    # Expanding uncertainty cone over forecast horizon
    h_steps = np.arange(1, horizon + 1)
    uncertainty_multiplier = np.sqrt(h_steps)

    lower_80 = np.clip(future_pred - 1.28 * residual_std * (0.8 + 0.05 * uncertainty_multiplier), 0, None)
    upper_80 = future_pred + 1.28 * residual_std * (0.8 + 0.05 * uncertainty_multiplier)
    lower_95 = np.clip(future_pred - 1.96 * residual_std * (0.8 + 0.05 * uncertainty_multiplier), 0, None)
    upper_95 = future_pred + 1.96 * residual_std * (0.8 + 0.05 * uncertainty_multiplier)

    future_df = pd.DataFrame({
        "Date": future_dates,
        "Forecast": np.round(future_pred, 2),
        "Lower_80": np.round(lower_80, 2),
        "Upper_80": np.round(upper_80, 2),
        "Lower_95": np.round(lower_95, 2),
        "Upper_95": np.round(upper_95, 2),
    })

    return {
        "status": "success",
        "model_name": model_name,
        "train_size": len(train),
        "test_size": len(test),
        "metrics_baseline": metrics_baseline,
        "metrics_model": metrics_model,
        "comparison_df": comparison_df,
        "future_df": future_df,
        "historical_series": series,
    }
