"""Shared paths, constants, and small helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS = PROJECT_ROOT / "outputs"
FORECASTS_DIR = OUTPUTS / "forecasts"
METRICS_DIR = OUTPUTS / "metrics"
PLOTS_DIR = OUTPUTS / "plots"

RAW_CSV_NAME = "indian_fmcg_retail_sales_2024.csv"

EXPECTED_COLUMNS = [
    "Invoice_ID",
    "Invoice_Date",
    "City",
    "Store_Format",
    "Category",
    "Brand",
    "Channel",
    "Payment_Mode",
    "Units",
    "Cost_Price",
    "Selling_Price",
    "Revenue",
    "Cost",
    "Margin",
    "Margin_%",
    "Stock_On_Hand",
    "Reorder_Level",
    "Lead_Time_Days",
    "Customer_Age",
    "Customer_Gender",
    "Loyalty_Flag",
]

NUMERIC_COLUMNS = [
    "Units",
    "Cost_Price",
    "Selling_Price",
    "Revenue",
    "Cost",
    "Margin",
    "Margin_%",
    "Stock_On_Hand",
    "Reorder_Level",
    "Lead_Time_Days",
    "Customer_Age",
    "Loyalty_Flag",
]

GRAIN_KEYS = ["Date", "Category"]
TARGET_COL = "Revenue"

# Chronological split for 2024 (dataset ends 2024-12-30).
TRAIN_END = pd.Timestamp("2024-10-31")
VALID_END = pd.Timestamp("2024-11-30")
TEST_END = pd.Timestamp("2024-12-30")

LAGS = [1, 7, 14, 30]
ROLLING_WINDOWS = [7, 14, 30]


def ensure_dirs() -> None:
    for path in [
        DATA_RAW,
        DATA_PROCESSED,
        MODELS_DIR,
        FORECASTS_DIR,
        METRICS_DIR,
        PLOTS_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(obj).isoformat()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) > 1e-8
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return float("nan")
    return float(np.sum(np.abs(y_true - y_pred)) / denom * 100)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))
