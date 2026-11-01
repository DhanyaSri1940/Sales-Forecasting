from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd
import xgboost as xgb

from src.utils import DATA_PROCESSED, FORECASTS_DIR, METRICS_DIR, MODELS_DIR, read_json


@lru_cache(maxsize=1)
def load_feature_spec() -> dict[str, Any]:
    return read_json(MODELS_DIR / "feature_spec.json")


@lru_cache(maxsize=1)
def load_booster() -> xgb.Booster:
    spec = load_feature_spec()
    booster = xgb.Booster()
    booster.load_model(spec["model_path"])
    return booster


@lru_cache(maxsize=1)
def load_metrics() -> dict[str, Any]:
    return read_json(METRICS_DIR / "metrics.json")


@lru_cache(maxsize=1)
def load_transactions() -> pd.DataFrame:
    path = DATA_PROCESSED / "transactions.pkl"
    if not path.exists():
        raise FileNotFoundError("Processed transactions not found. Run: python -m src.train")
    return pd.read_pickle(path)


@lru_cache(maxsize=1)
def load_panel() -> pd.DataFrame:
    df = pd.read_csv(DATA_PROCESSED / "forecast_panel.csv", parse_dates=["Date"])
    return df


@lru_cache(maxsize=1)
def load_future_forecast() -> pd.DataFrame:
    return pd.read_csv(FORECASTS_DIR / "future_forecast_30d.csv", parse_dates=["Date"])


@lru_cache(maxsize=1)
def load_test_predictions() -> pd.DataFrame:
    return pd.read_csv(FORECASTS_DIR / "test_predictions.csv", parse_dates=["Date"])


@lru_cache(maxsize=1)
def load_analytics_snapshot() -> dict[str, Any]:
    return read_json(DATA_PROCESSED / "analytics_snapshot.json")


@lru_cache(maxsize=1)
def load_inventory_risk() -> pd.DataFrame:
    path = DATA_PROCESSED / "inventory_risk.csv"
    if not path.exists():
        raise FileNotFoundError("Inventory table not found. Run: python -m src.train")
    return pd.read_csv(path)
