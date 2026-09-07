from fastapi import APIRouter

from app.api.v1 import (
    incidents,
    satellite,
    segmentation,
    ocean,
    ais,
    attribution,
    reports,
    evidence,
    system
)


api_router = APIRouter()


api_router.include_router(
    incidents.router,
    prefix="/incidents",
    tags=["Incidents"]
)

api_router.include_router(
    satellite.router,
    prefix="/satellite",
    tags=["Satellite SAR"]
)

api_router.include_router(
    segmentation.router,
    prefix="/segmentation",
    tags=["ML Segmentation"]
)

api_router.include_router(
    ocean.router,
    prefix="/ocean",
    tags=["Ocean Drift Modeling"]
)

api_router.include_router(
    ais.router,
    prefix="/ais",
    tags=["AIS Vessel Tracking"]
)

api_router.include_router(
    attribution.router,
    prefix="/attribution",
    tags=["Attribution Scoring"]
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Evidence Reports"]
)

api_router.include_router(
    evidence.router,
    prefix="/evidence",
    tags=["Evidence Locker"]
)

api_router.include_router(
    system.router,
    prefix="/system",
    tags=["System Telemetry"]
)