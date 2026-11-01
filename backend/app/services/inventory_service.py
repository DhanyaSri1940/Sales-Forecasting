from __future__ import annotations

from typing import Any

import pandas as pd

from backend.app.ml.model_loader import load_future_forecast, load_transactions
from backend.app.services.analytics_service import apply_filters
from src.business_analysis import INVENTORY_RULE, inventory_risk


def inventory_payload(**filters: str | None) -> dict[str, Any]:
    tx = apply_filters(load_transactions(), **filters)
    future = load_future_forecast()
    if filters.get("category"):
        future = future[future["Category"] == filters["category"]]
    table = inventory_risk(tx, future) if not tx.empty else pd.DataFrame()
    return {
        "rule": INVENTORY_RULE,
        "plain_rule": (
            "Needs attention: lower stock cover than other categories and a higher 30-day forecast. "
            "Watch: only one of those. In good shape: neither."
        ),
        "table": table.to_dict(orient="records"),
        "note": "Stock on hand is never zero in this file, so a stockout is not claimed.",
        "filters": {k: v for k, v in filters.items() if v},
    }
