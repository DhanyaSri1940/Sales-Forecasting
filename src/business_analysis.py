"""Deterministic business KPIs and contribution tables from actual transactions."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import DATA_PROCESSED, METRICS_DIR, write_json


def _contribution(tx: pd.DataFrame, col: str) -> pd.DataFrame:
    g = (
        tx.groupby(col, dropna=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Units=("Units", "sum"),
            Cost=("Cost", "sum"),
            Margin=("Margin", "sum"),
            Invoices=("Invoice_ID", "count"),
        )
        .reset_index()
    )
    g["Revenue_Share_%"] = g["Revenue"] / g["Revenue"].sum() * 100
    g["Margin_%"] = g["Margin"] / g["Revenue"]
    return g.sort_values("Revenue", ascending=False)


def monthly_revenue(tx: pd.DataFrame) -> pd.DataFrame:
    tmp = tx.copy()
    tmp["Month"] = pd.to_datetime(tmp["Date"]).dt.to_period("M").astype(str)
    m = tmp.groupby("Month", as_index=False).agg(Revenue=("Revenue", "sum"), Units=("Units", "sum"))
    m["MoM_Revenue_Growth_%"] = m["Revenue"].pct_change() * 100
    return m


def kpis(tx: pd.DataFrame) -> dict[str, Any]:
    total_revenue = float(tx["Revenue"].sum())
    total_cost = float(tx["Cost"].sum())
    total_margin = float(tx["Margin"].sum())
    invoices = int(len(tx))
    monthly = monthly_revenue(tx)
    latest_mom = monthly["MoM_Revenue_Growth_%"].dropna()
    return {
        "total_revenue": total_revenue,
        "total_units": int(tx["Units"].sum()),
        "total_cost": total_cost,
        "total_margin": total_margin,
        "average_margin_pct": float(total_margin / total_revenue) if total_revenue else None,
        "average_selling_price": float(tx["Selling_Price"].mean()),
        "average_invoice_value": float(total_revenue / invoices) if invoices else None,
        "invoice_count": invoices,
        "city_count": int(tx["City"].nunique()),
        "category_count": int(tx["Category"].nunique()),
        "brand_count": int(tx["Brand"].nunique()),
        "latest_mom_revenue_growth_pct": float(latest_mom.iloc[-1]) if len(latest_mom) else None,
        "date_min": str(pd.to_datetime(tx["Date"]).min().date()),
        "date_max": str(pd.to_datetime(tx["Date"]).max().date()),
        "customer_age_available_count": int(tx["Customer_Age"].notna().sum()),
        "customer_age_missing_count": int(tx["Customer_Age"].isna().sum()),
        "customer_gender_missing_count": int(tx["Customer_Gender"].isna().sum()),
    }


INVENTORY_RULE = (
    "Days of stock = typical stock on hand divided by typical daily units sold "
    "(at city × category, the same scale as the stock field). "
    "A category is compared with the other categories: "
    "Needs attention if days of stock are below the median and the 30-day sales forecast is above the median; "
    "Watch if only one of those is true; "
    "In good shape if neither is true. "
    "This is a relative ranking, not an observed stockout."
)


def inventory_risk(tx: pd.DataFrame, daily_category_forecast: pd.DataFrame | None = None) -> pd.DataFrame:
    """Simple relative stock-vs-forecast ranking by category."""
    stats = (
        tx.groupby("Category")
        .agg(
            avg_stock=("Stock_On_Hand", "mean"),
            avg_reorder=("Reorder_Level", "mean"),
            avg_lead=("Lead_Time_Days", "mean"),
        )
        .reset_index()
    )
    city_cat_daily = tx.groupby(["Date", "City", "Category"], as_index=False)["Units"].sum()
    typical_sales = city_cat_daily.groupby("Category")["Units"].mean().rename("typical_daily_sales")
    stats = stats.merge(typical_sales, on="Category", how="left")
    stats["days_of_stock"] = stats["avg_stock"] / stats["typical_daily_sales"]

    if daily_category_forecast is not None and not daily_category_forecast.empty:
        f = daily_category_forecast.groupby("Category", as_index=False)["Forecasted_Revenue"].sum()
        stats = stats.merge(f, on="Category", how="left")
    else:
        stats["Forecasted_Revenue"] = pd.NA

    med_days = float(stats["days_of_stock"].median())
    med_forecast = (
        float(stats["Forecasted_Revenue"].median())
        if stats["Forecasted_Revenue"].notna().any()
        else None
    )

    def _status(row: pd.Series) -> tuple[str, str]:
        low_stock = row["days_of_stock"] < med_days
        high_sales = (
            med_forecast is not None
            and pd.notna(row.get("Forecasted_Revenue"))
            and row["Forecasted_Revenue"] > med_forecast
        )
        if low_stock and high_sales:
            return "Needs attention", "Fewer days of stock than most categories, and a higher sales forecast."
        if low_stock:
            return "Watch", "Fewer days of stock than most categories."
        if high_sales:
            return "Watch", "Higher 30-day sales forecast than most categories."
        return "In good shape", "Stock cover and forecast are both in line with other categories."

    labelled = stats.apply(_status, axis=1, result_type="expand")
    stats["status"] = labelled[0]
    stats["why"] = labelled[1]
    stats["avg_stock"] = stats["avg_stock"].round(0)
    stats["typical_daily_sales"] = stats["typical_daily_sales"].round(0)
    stats["days_of_stock"] = stats["days_of_stock"].round(0)
    rank = {"Needs attention": 0, "Watch": 1, "In good shape": 2}
    stats["_rank"] = stats["status"].map(rank)
    return stats.sort_values(["_rank", "days_of_stock"]).drop(columns="_rank")


def build_analytics_payload(tx: pd.DataFrame) -> dict[str, Any]:
    payload = {
        "kpis": kpis(tx),
        "monthly_revenue": monthly_revenue(tx).to_dict(orient="records"),
        "categories": _contribution(tx, "Category").to_dict(orient="records"),
        "cities": _contribution(tx, "City").to_dict(orient="records"),
        "brands": _contribution(tx, "Brand").to_dict(orient="records"),
        "channels": _contribution(tx, "Channel").to_dict(orient="records"),
        "store_formats": _contribution(tx, "Store_Format").to_dict(orient="records"),
        "payment_modes": _contribution(tx, "Payment_Mode").to_dict(orient="records"),
        "loyalty": _contribution(tx, "Loyalty_Flag").to_dict(orient="records"),
        "unavailable_fields": [
            "Discount",
            "Advertising_Spend",
            "Marketing_Spend",
            "Holiday",
            "Weather",
            "Customer_Traffic",
            "Returns",
            "Wastage",
        ],
    }
    write_json(DATA_PROCESSED / "analytics_snapshot.json", payload)
    write_json(METRICS_DIR / "kpis.json", payload["kpis"])
    return payload
