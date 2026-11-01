from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.ml.model_loader import load_analytics_snapshot, load_future_forecast, load_transactions
from src.business_analysis import _contribution, inventory_risk, monthly_revenue


FILTER_COLUMNS = {
    "city": "City",
    "category": "Category",
    "brand": "Brand",
    "channel": "Channel",
    "store_format": "Store_Format",
    "payment_mode": "Payment_Mode",
}


def apply_filters(tx: pd.DataFrame, **filters: str | None) -> pd.DataFrame:
    out = tx
    for key, col in FILTER_COLUMNS.items():
        value = filters.get(key)
        if value:
            out = out[out[col] == value]
    return out


def dimension_table(dimension: str, **filters: str | None) -> list[dict[str, Any]]:
    allowed = {
        "categories": "Category",
        "cities": "City",
        "brands": "Brand",
        "channels": "Channel",
        "store_formats": "Store_Format",
        "payment_modes": "Payment_Mode",
        "loyalty": "Loyalty_Flag",
    }
    if dimension not in allowed:
        raise ValueError("Unknown analytics dimension")
    tx = apply_filters(load_transactions(), **filters)
    if tx.empty:
        return []
    return _contribution(tx, allowed[dimension]).to_dict(orient="records")


def daily_revenue(**filters: str | None) -> list[dict[str, Any]]:
    tx = apply_filters(load_transactions(), **filters)
    if tx.empty:
        return []
    g = tx.groupby("Date", as_index=False)["Revenue"].sum().sort_values("Date")
    g["Date"] = pd.to_datetime(g["Date"]).dt.strftime("%Y-%m-%d")
    return g.to_dict(orient="records")


def dashboard_bundle() -> dict[str, Any]:
    snap = load_analytics_snapshot()
    tx = load_transactions()
    daily = (
        tx.groupby("Date", as_index=False)["Revenue"].sum().sort_values("Date")
    )
    daily["Date"] = pd.to_datetime(daily["Date"]).dt.strftime("%Y-%m-%d")
    cats = snap["categories"][:8]
    insights = [
        f"{cats[0]['Category']} is the highest-revenue category at ₹{cats[0]['Revenue']:,.0f} ({cats[0]['Revenue_Share_%']:.1f}% of total).",
        f"{snap['cities'][0]['City']} leads city revenue at ₹{snap['cities'][0]['Revenue']:,.0f} ({snap['cities'][0]['Revenue_Share_%']:.1f}% of total).",
        f"{snap['brands'][0]['Brand']} is the highest-revenue brand at ₹{snap['brands'][0]['Revenue']:,.0f}.",
        f"Gross margin is {snap['kpis']['average_margin_pct']*100:.2f}% of revenue for the year.",
        f"Month-over-month revenue change in the latest complete month is {snap['kpis']['latest_mom_revenue_growth_pct']:.2f}%.",
    ]
    inv = inventory_risk(tx, load_future_forecast())
    attention = inv.loc[inv["status"] == "Needs attention", "Category"].tolist()
    if attention:
        insights.append(
            "Inventory check (relative ranking, not an observed stockout): "
            + ", ".join(attention)
            + " need attention — fewer days of stock than most categories, and a higher 30-day sales forecast."
        )
    return {
        "kpis": snap["kpis"],
        "daily_revenue": daily.to_dict(orient="records"),
        "monthly_revenue": snap["monthly_revenue"],
        "categories": snap["categories"],
        "cities": snap["cities"],
        "inventory_risk": inv.to_dict(orient="records"),
        "insights": insights,
        "dataset_note": (
            "Simulated/educational Indian FMCG retail dataset for calendar year 2024. "
            "It does not contain discount, advertising, marketing spend, weather, holidays, "
            "customer traffic, returns, or wastage."
        ),
    }


def monthly(**filters: str | None) -> list[dict[str, Any]]:
    tx = apply_filters(load_transactions(), **filters)
    if tx.empty:
        return []
    return monthly_revenue(tx).to_dict(orient="records")
