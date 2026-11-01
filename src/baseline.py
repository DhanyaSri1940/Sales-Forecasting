"""Simple chronological baselines evaluated on the same test window as XGBoost."""

from __future__ import annotations

import numpy as np
import pandas as pd


def naive_previous_period(series: pd.Series) -> pd.Series:
    return series.shift(1)


def moving_average(series: pd.Series, window: int = 7) -> pd.Series:
    return series.shift(1).rolling(window, min_periods=window).mean()


def seasonal_naive(series: pd.Series, season: int = 7) -> pd.Series:
    """Weekly seasonal naive: value from the same weekday last week."""
    return series.shift(season)


def baseline_predictions(history_and_eval: pd.Series, eval_index: pd.Index) -> dict[str, np.ndarray]:
    naive = naive_previous_period(history_and_eval)
    ma7 = moving_average(history_and_eval, 7)
    seas = seasonal_naive(history_and_eval, 7)
    return {
        "Naive previous-period": naive.loc[eval_index].to_numpy(),
        "Moving average (7-day)": ma7.loc[eval_index].to_numpy(),
        "Seasonal naive (7-day)": seas.loc[eval_index].to_numpy(),
    }
