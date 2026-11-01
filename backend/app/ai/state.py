from __future__ import annotations

from typing import Any, TypedDict


class InsightState(TypedDict, total=False):
    question: str
    retrieved: dict[str, Any]
    analysis: dict[str, Any]
    validation: dict[str, Any]
    answer: str
    grounded: bool
    unavailable: list[str]
