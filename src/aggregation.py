"""Aggregate transaction-level invoices into a forecasting panel."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import DATA_PROCESSED, GRAIN_KEYS, write_json


GRAIN_DECISION = {
    "selected_grain": "Date × Category",
    "target": "Daily Revenue",
    "options_evaluated": {
        "A_date_category": {
            "cells": 2920,
            "missing_cells": 0,
            "min_invoices_per_cell": 16,
            "median_invoices_per_cell": 34,
        },
        "B_date_city_category": {
            "cells": 23032,
            "missing_cells": 328,
            "min_invoices_per_cell": 1,
            "median_invoices_per_cell": 4,
        },
    },
    "rationale": (
        "Date × Category is the primary forecasting grain. Every category has sales on every "
        "calendar day in 2024 (zero sparsity), with at least 16 invoices per cell. "
        "Date × City × Category is more granular for local replenishment but is sparser "
        "(328 empty city-category-days, median 4 invoices) and noisier for daily revenue. "
        "City, brand, channel, and store-format views are produced by top-down allocation of "
        "category forecasts using trailing 30-day revenue shares. Assumption: recent mix is a "
        "reasonable allocator when the model is not trained at that grain."
    ),
}


def aggregate_forecast_panel(tx: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        tx.groupby(GRAIN_KEYS, as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Units=("Units", "sum"),
            Cost=("Cost", "sum"),
            Margin=("Margin", "sum"),
            Invoice_Count=("Invoice_ID", "count"),
            Average_Selling_Price=("Selling_Price", "mean"),
            Average_Cost=("Cost_Price", "mean"),
        )
        .sort_values(GRAIN_KEYS)
        .reset_index(drop=True)
    )
    grouped["Margin_%"] = grouped["Margin"] / grouped["Revenue"]
    return grouped


def grain_coverage_report(tx: pd.DataFrame) -> dict[str, Any]:
    dates = tx["Date"].nunique()
    cats = tx["Category"].nunique()
    cities = tx["City"].nunique()
    a = tx.groupby(["Date", "Category"]).size()
    b = tx.groupby(["Date", "City", "Category"]).size()
    return {
        "calendar_days": int(dates),
        "categories": int(cats),
        "cities": int(cities),
        "date_category_cells": int(len(a)),
        "date_category_expected": int(dates * cats),
        "date_category_missing": int(dates * cats - len(a)),
        "date_city_category_cells": int(len(b)),
        "date_city_category_expected": int(dates * cities * cats),
        "date_city_category_missing": int(dates * cities * cats - len(b)),
        "decision": GRAIN_DECISION,
    }


def save_panel(panel: pd.DataFrame) -> None:
    path = DATA_PROCESSED / "forecast_panel.csv"
    panel.to_csv(path, index=False)
    write_json(DATA_PROCESSED / "grain_decision.json", GRAIN_DECISION)
