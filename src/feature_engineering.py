"""Calendar, lag, and rolling features with explicit leakage controls."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import GRAIN_KEYS, LAGS, ROLLING_WINDOWS, TARGET_COL, write_json, DATA_PROCESSED


CALENDAR_FEATURES = [
    "year",
    "month",
    "quarter",
    "day",
    "day_of_week",
    "week_of_year",
    "is_weekend",
    "day_of_month",
    "is_month_start",
    "is_month_end",
]


LEAKAGE_AUDIT = {
    "A_safe_historical": [
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_7",
        "rolling_std_30",
        "rolling_min_7",
        "rolling_max_7",
    ],
    "B_known_in_advance": CALENDAR_FEATURES + ["Category"],
    "C_potentially_leaky": [
        "Stock_On_Hand",
        "Selling_Price",
        "Cost_Price",
        "Units",
        "Customer_Age",
        "Customer_Gender",
        "Loyalty_Flag",
        "Lead_Time_Days",
        "Reorder_Level",
    ],
    "D_target_derived": ["Revenue", "Cost", "Margin", "Margin_%"],
    "used_in_model": CALENDAR_FEATURES
    + [
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_7",
        "rolling_std_30",
        "rolling_min_7",
        "rolling_max_7",
        "Category",
    ],
    "excluded_and_why": {
        "same-day Revenue/Units/Margin/prices": "These are the outcome or are realized with the sale. Using them to predict same-day revenue is leakage.",
        "Stock_On_Hand / Reorder_Level / Lead_Time_Days": (
            "Inventory fields are recorded at invoice level. Aggregating them to a daily category "
            "forecast grain is ambiguous, and same-day stock is not treated as known at prediction time."
        ),
        "Customer_Age / Customer_Gender / Loyalty_Flag": (
            "Future customer mix is not known in advance. Age is also ~40% missing and is never imputed."
        ),
        "Brand / Channel / Store_Format / City / Payment_Mode": (
            "Not part of the selected Date × Category grain. Used in analytics and for top-down "
            "allocation shares, not as contemporaneous XGBoost features."
        ),
    },
    "rolling_implementation": "All rolling statistics use revenue.shift(1).rolling(window) so the current target is excluded.",
}


def add_calendar_features(df: pd.DataFrame, date_col: str = "Date") -> pd.DataFrame:
    out = df.copy()
    dt = pd.to_datetime(out[date_col])
    out["year"] = dt.dt.year
    out["month"] = dt.dt.month
    out["quarter"] = dt.dt.quarter
    out["day"] = dt.dt.day
    out["day_of_week"] = dt.dt.dayofweek
    out["week_of_year"] = dt.dt.isocalendar().week.astype(int)
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["day_of_month"] = dt.dt.day
    out["is_month_start"] = dt.dt.is_month_start.astype(int)
    out["is_month_end"] = dt.dt.is_month_end.astype(int)
    return out


def _grouped_rolling(shifted: pd.Series, groups: pd.Series, window: int, stat: str) -> pd.Series:
    rolled = shifted.groupby(groups, sort=False).rolling(window)
    agg = getattr(rolled, stat)()
    return agg.reset_index(level=0, drop=True)


def add_lag_and_rolling_features(
    panel: pd.DataFrame,
    group_cols: list[str] | None = None,
    target: str = TARGET_COL,
) -> pd.DataFrame:
    group_cols = group_cols or ["Category"]
    out = panel.sort_values(group_cols + ["Date"]).copy()
    grouped = out.groupby(group_cols, sort=False)[target]
    shifted = grouped.shift(1)
    group_key = out[group_cols[0]] if len(group_cols) == 1 else out[group_cols].astype(str).agg("|".join, axis=1)

    for lag in LAGS:
        out[f"lag_{lag}"] = grouped.shift(lag)

    out["rolling_mean_7"] = _grouped_rolling(shifted, group_key, 7, "mean")
    out["rolling_mean_14"] = _grouped_rolling(shifted, group_key, 14, "mean")
    out["rolling_mean_30"] = _grouped_rolling(shifted, group_key, 30, "mean")
    out["rolling_std_7"] = _grouped_rolling(shifted, group_key, 7, "std")
    out["rolling_std_30"] = _grouped_rolling(shifted, group_key, 30, "std")
    out["rolling_min_7"] = _grouped_rolling(shifted, group_key, 7, "min")
    out["rolling_max_7"] = _grouped_rolling(shifted, group_key, 7, "max")
    return out


def model_feature_columns() -> list[str]:
    return [
        *CALENDAR_FEATURES,
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_30",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_30",
        "rolling_std_7",
        "rolling_std_30",
        "rolling_min_7",
        "rolling_max_7",
        "Category",
    ]


def prepare_model_frame(panel: pd.DataFrame) -> pd.DataFrame:
    featured = add_calendar_features(panel)
    featured = add_lag_and_rolling_features(featured)
    feature_cols = [c for c in model_feature_columns() if c != "Category"]
    featured = featured.dropna(subset=feature_cols).reset_index(drop=True)
    write_json(DATA_PROCESSED / "leakage_audit.json", LEAKAGE_AUDIT)
    return featured


def assert_no_future_leakage(featured: pd.DataFrame) -> None:
    """lag_1 on date t must equal revenue on date t-1 for the same category."""
    sample = featured.sort_values(["Category", "Date"])
    prev = sample.groupby("Category")["Revenue"].shift(1)
    mismatch = (sample["lag_1"] - prev).abs() > 1e-6
    mismatch = mismatch & sample["lag_1"].notna() & prev.notna()
    if bool(mismatch.any()):
        raise AssertionError("lag_1 does not match previous-day revenue; possible leakage in lag generation.")
