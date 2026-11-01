from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.services.inventory_service import inventory_payload

router = APIRouter()


@router.get("/inventory/risk")
def get_inventory(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
):
    try:
        return inventory_payload(
            city=city,
            category=category,
            brand=brand,
            channel=channel,
            store_format=store_format,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
