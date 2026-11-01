from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.ml.model_loader import load_metrics
from backend.app.schemas.response_models import DashboardResponse, KPIResponse
from backend.app.services.analytics_service import dashboard_bundle
from backend.app.services.forecasting_service import forecast_payload, test_actual_vs_forecast

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard():
    try:
        bundle = dashboard_bundle()
        fc = forecast_payload(horizon=14)
        metrics = load_metrics()
        kpis = dict(bundle["kpis"])
        kpis["forecasted_revenue"] = fc["forecast_total"]
        kpis["forecast_horizon_days"] = 14
        kpis["forecast_error_mae"] = metrics["xgboost_test"]["MAE"]
        kpis["forecast_error_wape"] = metrics["xgboost_test"]["WAPE"]
        return {
            **bundle,
            "kpis": KPIResponse(**kpis),
            "test_actual_vs_forecast": test_actual_vs_forecast(),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
