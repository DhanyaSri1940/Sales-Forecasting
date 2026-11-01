from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.response_models import ForecastResponse
from backend.app.services.forecasting_service import ALLOWED_HORIZONS, forecast_payload

router = APIRouter()


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    horizon: int = Query(14, description="Forecast horizon in days"),
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = Query(None, alias="store_format"),
):
    if horizon not in ALLOWED_HORIZONS:
        raise HTTPException(status_code=422, detail="horizon must be 7, 14, or 30")
    try:
        payload = forecast_payload(
            horizon=horizon,
            city=city,
            category=category,
            brand=brand,
            channel=channel,
            store_format=store_format,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not payload["historical"] and payload["forecast_total"] == 0:
        raise HTTPException(status_code=404, detail="No rows match the selected filters.")
    return payload
