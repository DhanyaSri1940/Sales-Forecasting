"""Metrics and comparison tables."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils import mae, mape, rmse, wape


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "MAE": round(mae(y_true, y_pred), 4),
        "RMSE": round(rmse(y_true, y_pred), 4),
        "MAPE": round(mape(y_true, y_pred), 4),
        "WAPE": round(wape(y_true, y_pred), 4),
    }


def metrics_table(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows)
