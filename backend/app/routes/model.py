from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.ai.graph import run_insight
from backend.app.ml.model_loader import load_metrics
from backend.app.schemas.response_models import InsightRequest, InsightResponse, ModelPerformanceResponse

router = APIRouter()

METRIC_EXPLANATIONS = {
    "MAE": "Mean Absolute Error: average absolute difference between actual and predicted revenue at the Date × Category grain.",
    "RMSE": "Root Mean Squared Error: penalizes larger misses more than MAE, still in revenue units.",
    "MAPE": "Mean Absolute Percentage Error: average absolute percent error. Unstable if actuals are near zero; this panel has no zero-revenue category-days.",
    "WAPE": "Weighted Absolute Percentage Error: total absolute error divided by total actual revenue. More stable than MAPE for summing across days.",
}


@router.get("/model/performance", response_model=ModelPerformanceResponse)
def performance():
    try:
        metrics = load_metrics()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        **metrics,
        "metric_explanations": METRIC_EXPLANATIONS,
    }


@router.get("/model/features")
def features():
    try:
        metrics = load_metrics()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "importance": metrics["feature_importance"][:15],
        "note": (
            "Feature importance indicates predictive usefulness in the XGBoost model. "
            "It does not prove causation."
        ),
        "hyperparameter_notes": metrics["hyperparameter_notes"],
        "leakage_audit_summary": metrics["leakage_audit_summary"],
    }


@router.post("/insights", response_model=InsightResponse)
def insights(body: InsightRequest):
    result = run_insight(body.question)
    return {
        "question": body.question,
        "answer": result.get("answer", "Not available in the current dataset."),
        "grounded": bool(result.get("grounded")),
        "used_metrics": result.get("analysis") or {},
        "unavailable": result.get("unavailable") or [],
    }
