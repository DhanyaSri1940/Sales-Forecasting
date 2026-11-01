from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.ml.model_loader import (
    load_feature_spec,
    load_future_forecast,
    load_metrics,
    load_panel,
    load_test_predictions,
    load_transactions,
)
from backend.app.services.analytics_service import apply_filters


ALLOWED_HORIZONS = {7, 14, 30}
HISTORY_LOOKBACK_BY_HORIZON = {7: 7, 14: 14, 30: 30}
SHARE_WINDOW_DAYS = 30
ALLOCATION_NOTE = (
    "Assumption: city, brand, channel, and store-format forecast views are allocated from "
    "Date × Category XGBoost forecasts using each slice's trailing 30-day revenue share. "
    "The model itself predicts category-level daily revenue."
)


def _shares(tx: pd.DataFrame, col: str, within: str | None = None) -> pd.Series:
    end = pd.to_datetime(tx["Date"]).max()
    start = end - pd.Timedelta(days=SHARE_WINDOW_DAYS - 1)
    window = tx[(pd.to_datetime(tx["Date"]) >= start) & (pd.to_datetime(tx["Date"]) <= end)]
    if window.empty:
        window = tx
    if within:
        totals = window.groupby([within, col])["Revenue"].sum()
        parent = window.groupby(within)["Revenue"].sum()
        return totals / parent
    s = window.groupby(col)["Revenue"].sum()
    return s / s.sum()


def _allocate(forecast: pd.DataFrame, tx: pd.DataFrame, filters: dict[str, str | None]) -> tuple[pd.DataFrame, str | None]:
    out = forecast.copy()
    note = None
    city, brand, channel, store_format = (
        filters.get("city"),
        filters.get("brand"),
        filters.get("channel"),
        filters.get("store_format"),
    )
    if city:
        shares = _shares(tx, "City", within="Category")
        out["Forecasted_Revenue"] = out.apply(
            lambda r: r["Forecasted_Revenue"] * float(shares.get((r["Category"], city), 0.0)),
            axis=1,
        )
        note = ALLOCATION_NOTE
    extra_filters = [("Brand", brand), ("Channel", channel), ("Store_Format", store_format)]
    active = [(col, val) for col, val in extra_filters if val]
    if active:
        note = ALLOCATION_NOTE
        for col, val in active:
            if city or filters.get("category"):
                # share of the remaining slice
                slice_tx = tx
                if city:
                    slice_tx = slice_tx[slice_tx["City"] == city]
                if filters.get("category"):
                    slice_tx = slice_tx[slice_tx["Category"] == filters["category"]]
                share_map = _shares(slice_tx, col)
                factor = float(share_map.get(val, 0.0))
                out["Forecasted_Revenue"] = out["Forecasted_Revenue"] * factor
            else:
                shares = _shares(tx, col, within="Category")
                out["Forecasted_Revenue"] = out.apply(
                    lambda r, col=col, val=val, shares=shares: r["Forecasted_Revenue"]
                    * float(shares.get((r["Category"], val), 0.0)),
                    axis=1,
                )
    if filters.get("category"):
        out = out[out["Category"] == filters["category"]]
    return out, note


def forecast_payload(
    horizon: int = 14,
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
) -> dict[str, Any]:
    if horizon not in ALLOWED_HORIZONS:
        raise ValueError("horizon must be 7, 14, or 30")

    filters = {
        "city": city,
        "category": category,
        "brand": brand,
        "channel": channel,
        "store_format": store_format,
    }
    tx = load_transactions()
    panel = load_panel()
    future = load_future_forecast()
    future = future[future["horizon_day"] <= horizon].copy()

    hist_tx = apply_filters(tx, **filters)
    historical = []
    lookback = []
    prev_total = None
    if not hist_tx.empty:
        historical_df = (
            hist_tx.groupby("Date", as_index=False)["Revenue"].sum().sort_values("Date")
        )
        historical_df["Date"] = pd.to_datetime(historical_df["Date"]).dt.strftime("%Y-%m-%d")
        historical = historical_df.rename(columns={"Revenue": "Actual_Revenue"}).to_dict(orient="records")
        lookback = historical[-HISTORY_LOOKBACK_BY_HORIZON[int(horizon)] :]
        last = pd.to_datetime(hist_tx["Date"]).max()
        prev_start = last - pd.Timedelta(days=horizon - 1)
        prev_total = float(
            hist_tx.loc[
                (pd.to_datetime(hist_tx["Date"]) >= prev_start)
                & (pd.to_datetime(hist_tx["Date"]) <= last),
                "Revenue",
            ].sum()
        )

    allocated, note = _allocate(future, tx, filters)
    daily = allocated.groupby("Date", as_index=False)["Forecasted_Revenue"].sum().sort_values("Date")
    daily["Date"] = pd.to_datetime(daily["Date"]).dt.strftime("%Y-%m-%d")
    forecast_total = float(daily["Forecasted_Revenue"].sum())
    growth = None
    change = None
    if prev_total is not None and prev_total != 0:
        change = forecast_total - prev_total
        growth = (forecast_total / prev_total - 1) * 100

    spec = load_feature_spec()
    return {
        "grain": " × ".join(spec["grain"]),
        "horizon": horizon,
        "filters": {k: v for k, v in filters.items() if v},
        "historical": lookback,
        "forecast": daily.to_dict(orient="records"),
        "previous_period_actual": prev_total,
        "forecast_total": forecast_total,
        "change_from_previous_period": change,
        "forecasted_growth_pct": growth,
        "allocation_note": note,
        "recursive_note": load_metrics()["recursive_forecast_note"],
    }


def test_actual_vs_forecast() -> list[dict[str, Any]]:
    df = load_test_predictions()
    g = df.groupby("Date", as_index=False).agg(Actual=("Revenue", "sum"), Forecast=("Predicted_Revenue", "sum"))
    g["Date"] = pd.to_datetime(g["Date"]).dt.strftime("%Y-%m-%d")
    return g.to_dict(orient="records")
