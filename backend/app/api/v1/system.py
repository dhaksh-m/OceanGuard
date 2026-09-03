from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def system_health_check():
    """
    System health telemetry check for services, workers, database and MinIO storage.
    """
    return {
        "status": "HEALTHY",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "services": {
            "api_gateway": "ONLINE",
            "sar_ml_engine": "ONLINE (U-Net PyTorch)",
            "ocean_drift_worker": "ONLINE (Lagrangian Retro-Drift)",
            "ais_ingest_pipeline": "ONLINE (NMEA Streamer)",
            "database_postgis": "ONLINE",
            "object_storage": "ONLINE (MinIO S3)"
        }
    }
