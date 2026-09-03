import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OceanGuard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Cors
    ALLOWED_ORIGINS: list = ["*"]

    # Attribution weights
    WEIGHT_SPATIAL: float = 0.25
    WEIGHT_TEMPORAL: float = 0.20
    WEIGHT_TRAJECTORY: float = 0.20
    WEIGHT_SPEED: float = 0.10
    WEIGHT_HEADING: float = 0.10
    WEIGHT_AIS_ANOMALY: float = 0.10
    WEIGHT_VESSEL_CONTEXT: float = 0.05

settings = Settings()
