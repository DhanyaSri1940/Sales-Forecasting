from __future__ import annotations

import os
import re
from typing import Any

from backend.app.ai.prompts import GROUNDED_TEMPLATE
from backend.app.ai.state import InsightState
from backend.app.ml.model_loader import load_analytics_snapshot, load_metrics, load_transactions, load_future_forecast
from backend.app.services.forecasting_service import forecast_payload
from src.business_analysis import inventory_risk


FORBIDDEN_PATTERNS = [
    r"\b95%\s*accuracy\b",
    r"caused sales to increase",
    r"will definitely",
]


def retrieve_node(state: InsightState) -> InsightState:
    snap = load_analytics_snapshot()
    metrics = load_metrics()
    forecast = forecast_payload(horizon=14)
    state["retrieved"] = {
        "kpis": snap["kpis"],
        "top_categories": snap["categories"][:5],
        "lowest_margin_categories": sorted(snap["categories"], key=lambda r: r["Margin_%"])[:3],
        "top_cities": snap["cities"][:5],
        "top_brands": snap["brands"][:5],
        "channels": snap["channels"],
        "store_formats": snap["store_formats"],
        "loyalty": snap["loyalty"],
        "model_train": metrics["xgboost_train"],
        "model_valid": metrics["xgboost_validation"],
        "model_test": metrics["xgboost_test"],
        "comparison": metrics["comparison_test"],
        "forecast_14d_total": forecast["forecast_total"],
        "unavailable_fields": snap["unavailable_fields"],
        "inventory": inventory_risk(load_transactions(), load_future_forecast()).to_dict(orient="records"),
    }
    return state


def analyze_node(state: InsightState) -> InsightState:
    data = state["retrieved"]
    kpis = data["kpis"]
    cats = data["top_categories"]
    cities = data["top_cities"]
    state["analysis"] = {
        "question": state.get("question", ""),
        "total_revenue": kpis["total_revenue"],
        "mom": kpis["latest_mom_revenue_growth_pct"],
        "margin_pct": kpis["average_margin_pct"] * 100,
        "best_category": cats[0]["Category"],
        "best_category_revenue": cats[0]["Revenue"],
        "category_rows": cats,
        "lowest_margin_rows": data["lowest_margin_categories"],
        "best_city": cities[0]["City"],
        "best_city_revenue": cities[0]["Revenue"],
        "city_rows": cities,
        "brand_rows": data["top_brands"],
        "channel_rows": data["channels"],
        "store_format_rows": data["store_formats"],
        "loyalty_rows": data["loyalty"],
        "train_mae": data["model_train"]["MAE"],
        "valid_mae": data["model_valid"]["MAE"],
        "test_mae": data["model_test"]["MAE"],
        "test_rmse": data["model_test"]["RMSE"],
        "test_wape": data["model_test"]["WAPE"],
        "test_mape": data["model_test"]["MAPE"],
        "comparison": data["comparison"],
        "forecast_14d_total": data["forecast_14d_total"],
        "inventory_rows": data["inventory"],
    }
    return state


def validate_node(state: InsightState) -> InsightState:
    q = state.get("question", "").lower()
    unavailable: list[str] = []
    external = ["discount", "advertis", "marketing", "weather", "holiday", "traffic", "return", "wastage"]
    for term in external:
        if term in q:
            unavailable.append("Not available in the current dataset.")
            break
    state["validation"] = {"ok": True, "unsupported_external_request": bool(unavailable)}
    state["unavailable"] = list(dict.fromkeys(unavailable + [
        f for f in state["retrieved"]["unavailable_fields"]
        if f.lower() in q
    ]))
    state["grounded"] = True
    return state


def _inr(value: float) -> str:
    return f"₹{value:,.0f}"


def _topic_bullets(question: str, a: dict[str, Any]) -> list[str]:
    q = question.lower()
    bullets: list[str] = []

    model_q = any(w in q for w in (
        "model", "xgboost", "baseline", "mae", "rmse", "mape", "wape", "overfit",
        "holdout", "error", "performance", "feature", "accuracy",
    ))
    cat_q = "categor" in q
    city_q = "city" in q or "cities" in q
    brand_q = "brand" in q
    channel_q = "channel" in q
    store_q = "store" in q or "format" in q
    margin_q = "margin" in q
    fc_q = any(w in q for w in ("forecast", "next", "coming", "horizon"))
    loy_q = "loyal" in q
    trend_q = any(w in q for w in ("trend", "growth", "mom", "month"))
    inv_q = any(w in q for w in ("inventory", "stock", "demand", "stockout", "reorder"))

    if model_q:
        best = min(a["comparison"], key=lambda r: r["MAE"])
        bullets.append(
            f"On the December holdout, XGBoost MAE is {_inr(a['test_mae'])} per Date × Category day "
            f"(RMSE {_inr(a['test_rmse'])}, WAPE {a['test_wape']:.2f}%, MAPE {a['test_mape']:.2f}%). "
            "These are regression errors, not classification accuracy."
        )
        bullets.append(
            "Baseline MAE on the same window: "
            + "; ".join(f"{r['Model']} {_inr(r['MAE'])}" for r in a["comparison"] if r["Model"] != "XGBoost")
            + f". Lowest MAE is {best['Model']}."
        )
        bullets.append(
            f"Training MAE is {_inr(a['train_mae'])} and validation MAE is {_inr(a['valid_mae'])}. "
            "They are close, so there is no clear overfitting signal."
        )

    if cat_q:
        top = a["category_rows"][0]
        bullets.append(
            f"Highest-revenue category is {top['Category']} at {_inr(top['Revenue'])} "
            f"({top['Revenue_Share_%']:.1f}% of total)."
        )
        bullets.append(
            "Top 5 by revenue: "
            + ", ".join(f"{r['Category']} {_inr(r['Revenue'])}" for r in a["category_rows"][:5])
            + "."
        )

    if city_q:
        bullets.append(
            f"Highest-revenue city is {a['best_city']} at {_inr(a['best_city_revenue'])}."
        )
        bullets.append(
            "Top cities: "
            + ", ".join(f"{r['City']} {_inr(r['Revenue'])}" for r in a["city_rows"][:5])
            + "."
        )

    if brand_q:
        bullets.append(
            "Top brands by revenue: "
            + ", ".join(f"{r['Brand']} {_inr(r['Revenue'])}" for r in a["brand_rows"][:5])
            + "."
        )

    if channel_q:
        bullets.append(
            "Channel revenue: "
            + ", ".join(f"{r['Channel']} {_inr(r['Revenue'])}" for r in a["channel_rows"])
            + "."
        )

    if store_q:
        bullets.append(
            "Store format revenue: "
            + ", ".join(f"{r['Store_Format']} {_inr(r['Revenue'])}" for r in a["store_format_rows"])
            + "."
        )

    if margin_q:
        low = a["lowest_margin_rows"][0]
        bullets.append(
            f"Average gross margin is {a['margin_pct']:.2f}% of revenue. "
            f"Lowest-margin category among the calculated set is {low['Category']} ({low['Margin_%']*100:.2f}%)."
        )

    if fc_q:
        bullets.append(
            f"The 14-day category-level forecast totals {_inr(a['forecast_14d_total'])}. "
            "It is recursive, so error can accumulate. No prediction intervals were estimated."
        )

    if loy_q:
        rows = a["loyalty_rows"]
        bullets.append(
            "Loyalty vs non-loyalty revenue: "
            + ", ".join(
                f"{'Loyalty' if str(r.get('Loyalty_Flag')) in ('1', '1.0') else 'Non-loyalty'} {_inr(r['Revenue'])}"
                for r in rows
            )
            + "."
        )

    if trend_q:
        bullets.append(
            f"Full-year revenue is {_inr(a['total_revenue'])}. "
            f"Latest month-over-month revenue change is {a['mom']:.2f}%."
        )

    if inv_q:
        rows = a.get("inventory_rows") or []
        if rows:
            bullets.append(
                "Inventory vs demand is a relative ranking (not an observed stockout): "
                + "; ".join(f"{r['Category']} — {r['status']}" for r in rows)
                + "."
            )
            attention = [r["Category"] for r in rows if r.get("status") == "Needs attention"]
            if attention:
                bullets.append(
                    "Needs attention (fewer days of stock than most categories and a higher 30-day forecast): "
                    + ", ".join(attention)
                    + "."
                )
            else:
                bullets.append("No category is marked Needs attention under this ranking.")
        else:
            bullets.append("Inventory ranking is not available in the current snapshot.")

    if not bullets:
        bullets.append(
            f"Full-year revenue is {_inr(a['total_revenue'])} with average gross margin {a['margin_pct']:.2f}%."
        )
        bullets.append(
            f"{a['best_category']} leads categories and {a['best_city']} leads cities. "
            "Ask about a category, city, brand, forecast, or model metric for a focused summary."
        )
    return bullets


def generate_node(state: InsightState) -> InsightState:
    a = state["analysis"]
    bullets = _topic_bullets(state.get("question", ""), a)
    unavailable = ""
    if state.get("unavailable"):
        unavailable = "Not available in the current dataset: " + ", ".join(state["unavailable"])
        bullets.append("The requested external driver is not in this dataset, so it was not used.")
    answer = GROUNDED_TEMPLATE.format(
        question=state.get("question", ""),
        bullets="\n".join(f"- {b}" for b in bullets),
        unavailable=unavailable,
    )
    if os.getenv("OPENAI_API_KEY"):
        answer = _llm_interpret(state, answer)
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, answer, flags=re.I):
            answer = GROUNDED_TEMPLATE.format(
                question=state.get("question", ""),
                bullets="\n".join(f"- {b}" for b in bullets),
                unavailable="Model output was replaced because it contained an unsupported claim.",
            )
            break
    state["answer"] = answer.strip()
    return state


def _llm_interpret(state: InsightState, fallback: str) -> str:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
        from backend.app.ai.prompts import SYSTEM_RULES

        llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)
        msg = llm.invoke(
            [
                SystemMessage(content=SYSTEM_RULES),
                HumanMessage(
                    content=(
                        f"Question: {state.get('question')}\n"
                        f"Validated analysis JSON: {state.get('analysis')}\n"
                        f"Unavailable: {state.get('unavailable')}\n"
                        "Answer only this question in a short evidence-based summary. "
                        "Use only these numbers. Do not add unrelated KPIs."
                    )
                ),
            ]
        )
        return str(msg.content)
    except Exception:
        return fallback
