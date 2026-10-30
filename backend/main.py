"""
FastAPI main application entry point.
Mounts all routers and configures CORS for the React frontend.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    kpis, sales, customers, forecast, segmentation,
    anomalies, recommendations, admin, chat, insights, explorer
)
import backend.data_service as ds

app = FastAPI(
    title="AI E-Commerce Insights API",
    description="REST API powering the React e-commerce analytics dashboard.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-load dataset on startup
@app.on_event("startup")
async def startup_event():
    ds.get_df()

# Mount routers
app.include_router(kpis.router,            prefix="/api/kpis",            tags=["KPIs"])
app.include_router(sales.router,           prefix="/api/sales",           tags=["Sales"])
app.include_router(customers.router,       prefix="/api/customers",       tags=["Customers"])
app.include_router(forecast.router,        prefix="/api/forecast",        tags=["Forecast"])
app.include_router(segmentation.router,    prefix="/api/segmentation",    tags=["Segmentation"])
app.include_router(anomalies.router,       prefix="/api/anomalies",       tags=["Anomalies"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(insights.router,        prefix="/api/insights",        tags=["Insights"])
app.include_router(explorer.router,        prefix="/api/explorer",        tags=["Explorer"])
app.include_router(admin.router,           prefix="/api/admin",           tags=["Admin"])
app.include_router(chat.router,            prefix="/api/chat",            tags=["Chat"])

@app.get("/")
def root():
    return {"status": "ok", "message": "AI E-Commerce Insights API is running."}
