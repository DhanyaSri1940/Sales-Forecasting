from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.routes.analytics import router as analytics_router
from backend.app.routes.dashboard import router as dashboard_router
from backend.app.routes.forecast import router as forecast_router
from backend.app.routes.inventory import router as inventory_router
from backend.app.routes.model import router as model_router

app = FastAPI(
    title="Indian FMCG Sales Intelligence & Forecasting Platform",
    version="1.0.0",
    description="XGBoost sales forecasting with retail analytics for a simulated 2024 Indian FMCG dataset.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(dashboard_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(model_router, prefix="/api")
