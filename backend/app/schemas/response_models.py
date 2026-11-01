from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class KPIResponse(BaseModel):
    total_revenue: float
    total_units: int
    total_cost: float
    total_margin: float
    average_margin_pct: Optional[float]
    average_selling_price: float
    average_invoice_value: Optional[float]
    invoice_count: int
    city_count: int
    category_count: int
    brand_count: int
    latest_mom_revenue_growth_pct: Optional[float]
    date_min: str
    date_max: str
    forecasted_revenue: Optional[float] = None
    forecast_horizon_days: Optional[int] = None
    forecast_error_mae: Optional[float] = None
    forecast_error_wape: Optional[float] = None
    customer_age_available_count: int
    customer_age_missing_count: int
    customer_gender_missing_count: int


class DashboardResponse(BaseModel):
    kpis: KPIResponse
    daily_revenue: list[dict[str, Any]]
    monthly_revenue: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    cities: list[dict[str, Any]]
    insights: list[str]
    inventory_risk: list[dict[str, Any]] = []
    test_actual_vs_forecast: list[dict[str, Any]]
    dataset_note: str


class ForecastResponse(BaseModel):
    grain: str
    horizon: int
    filters: dict[str, Any]
    historical: list[dict[str, Any]]
    forecast: list[dict[str, Any]]
    previous_period_actual: Optional[float]
    forecast_total: float
    change_from_previous_period: Optional[float]
    forecasted_growth_pct: Optional[float]
    allocation_note: Optional[str] = None
    recursive_note: str


class ModelPerformanceResponse(BaseModel):
    split: dict[str, Any]
    xgboost_train: dict[str, float]
    xgboost_validation: dict[str, float]
    xgboost_test: dict[str, float]
    comparison_test: list[dict[str, Any]]
    feature_importance: list[dict[str, Any]]
    best_hyperparameters: dict[str, Any]
    hyperparameter_notes: dict[str, str]
    overfitting_note: Optional[str]
    metric_explanations: dict[str, str]
    recursive_forecast_note: str


class InsightRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class InsightResponse(BaseModel):
    question: str
    answer: str
    grounded: bool
    used_metrics: dict[str, Any]
    unavailable: list[str]
