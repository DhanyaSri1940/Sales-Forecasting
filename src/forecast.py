"""Recursive multi-step forecasting from the last observed Date × Category panel."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb

from src.feature_engineering import add_calendar_features, model_feature_columns
from src.utils import LAGS, TARGET_COL


def recursive_forecast(
    history: pd.DataFrame,
    booster: xgb.Booster,
    category_encoder: dict[str, int],
    horizon: int,
) -> pd.DataFrame:
    """Forecast `horizon` days beyond history['Date'].max() for every category.

    Predictions are appended and used to build subsequent lag/rolling features.
    Actual future revenue is never used.
    """
    if horizon not in (7, 14, 30):
        raise ValueError("horizon must be 7, 14, or 30")

    hist = history.sort_values(["Category", "Date"]).copy()
    last_date = pd.Timestamp(hist["Date"].max())
    categories = sorted(hist["Category"].unique().tolist())
    feature_cols = model_feature_columns()

    working = {cat: hist.loc[hist["Category"] == cat, ["Date", TARGET_COL]].copy() for cat in categories}
    rows: list[dict[str, Any]] = []

    for step in range(1, horizon + 1):
        forecast_date = last_date + pd.Timedelta(days=step)
        for cat in categories:
            series = working[cat]
            y = series[TARGET_COL].to_numpy(dtype=float)
            feat = _features_from_series(forecast_date, cat, y, category_encoder)
            dmat = xgb.DMatrix(
                np.array([feat[c] for c in feature_cols], dtype=float).reshape(1, -1),
                feature_names=feature_cols,
            )
            pred = float(booster.predict(dmat)[0])
            pred = max(pred, 0.0)
            working[cat] = pd.concat(
                [series, pd.DataFrame({"Date": [forecast_date], TARGET_COL: [pred]})],
                ignore_index=True,
            )
            rows.append(
                {
                    "Date": forecast_date,
                    "Category": cat,
                    "Forecasted_Revenue": pred,
                    "horizon_day": step,
                }
            )
    return pd.DataFrame(rows)


def _features_from_series(
    forecast_date: pd.Timestamp,
    category: str,
    y: np.ndarray,
    category_encoder: dict[str, int],
) -> dict[str, float]:
    cal = add_calendar_features(pd.DataFrame({"Date": [forecast_date], "Category": [category]})).iloc[0]
    out: dict[str, float] = {name: float(cal[name]) for name in [
        "year", "month", "quarter", "day", "day_of_week", "week_of_year",
        "is_weekend", "day_of_month", "is_month_start", "is_month_end",
    ]}
    out["Category"] = float(category_encoder[category])
    for lag in LAGS:
        out[f"lag_{lag}"] = float(y[-lag]) if len(y) >= lag else float("nan")
    shifted = y  # already historical relative to forecast_date
    def _roll(window: int, fn) -> float:
        if len(shifted) < window:
            return float("nan")
        return float(fn(shifted[-window:]))

    out["rolling_mean_7"] = _roll(7, np.mean)
    out["rolling_mean_14"] = _roll(14, np.mean)
    out["rolling_mean_30"] = _roll(30, np.mean)
    out["rolling_std_7"] = _roll(7, np.std)
    out["rolling_std_30"] = _roll(30, np.std)
    out["rolling_min_7"] = _roll(7, np.min)
    out["rolling_max_7"] = _roll(7, np.max)
    return out
