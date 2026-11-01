from __future__ import annotations

from fastapi import APIRouter

from backend.app.services.analytics_service import daily_revenue, dimension_table, monthly

router = APIRouter()


def _params(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
) -> dict[str, str | None]:
    return {
        "city": city,
        "category": category,
        "brand": brand,
        "channel": channel,
        "store_format": store_format,
        "payment_mode": payment_mode,
    }


@router.get("/analytics/categories")
def categories(
    city: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return dimension_table("categories", **_params(city=city, brand=brand, channel=channel, store_format=store_format, payment_mode=payment_mode))


@router.get("/analytics/cities")
def cities(
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return dimension_table("cities", **_params(category=category, brand=brand, channel=channel, store_format=store_format, payment_mode=payment_mode))


@router.get("/analytics/brands")
def brands(
    city: str | None = None,
    category: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return dimension_table("brands", **_params(city=city, category=category, channel=channel, store_format=store_format, payment_mode=payment_mode))


@router.get("/analytics/channels")
def channels(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return dimension_table("channels", **_params(city=city, category=category, brand=brand, store_format=store_format, payment_mode=payment_mode))


@router.get("/analytics/store-formats")
def store_formats(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    payment_mode: str | None = None,
):
    return dimension_table("store_formats", **_params(city=city, category=category, brand=brand, channel=channel, payment_mode=payment_mode))


@router.get("/analytics/payment-modes")
def payment_modes(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
):
    return dimension_table("payment_modes", **_params(city=city, category=category, brand=brand, channel=channel, store_format=store_format))


@router.get("/analytics/daily")
def daily(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return daily_revenue(**_params(city=city, category=category, brand=brand, channel=channel, store_format=store_format, payment_mode=payment_mode))


@router.get("/analytics/monthly")
def monthly_route(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return monthly(**_params(city=city, category=category, brand=brand, channel=channel, store_format=store_format, payment_mode=payment_mode))


@router.get("/analytics/loyalty")
def loyalty(
    city: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    channel: str | None = None,
    store_format: str | None = None,
    payment_mode: str | None = None,
):
    return dimension_table("loyalty", **_params(city=city, category=category, brand=brand, channel=channel, store_format=store_format, payment_mode=payment_mode))
