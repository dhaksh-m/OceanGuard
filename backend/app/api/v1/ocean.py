from fastapi import APIRouter
from app.models.schemas import OceanDriftResult
from ocean.drift_simulation import OceanDriftEngine

router = APIRouter()
drift_engine = OceanDriftEngine()

@router.post("/drift", response_model=OceanDriftResult)
def simulate_ocean_drift(
    incident_id: str = "INC-2026-0901",
    lat: float = 1.3120,
    lon: float = 103.8540,
    slick_age_hours: float = 5.5
):
    """
    Run particle-based ocean drift hindcast (probable origin zone) and forward forecast (24h/48h drift paths).
    """
    res = drift_engine.run_simulation(slick_centroid=(lat, lon), slick_age_hours=slick_age_hours)
    
    return {
        "incident_id": incident_id,
        "simulated_at": res["simulated_at"],
        "wind_speed_knots": res["environmental_conditions"]["wind_speed_knots"],
        "wind_direction_deg": res["environmental_conditions"]["wind_direction_deg"],
        "current_speed_knots": res["environmental_conditions"]["current_speed_knots"],
        "current_direction_deg": res["environmental_conditions"]["current_direction_deg"],
        "origin_zone_geojson": res["origin_zone_geojson"],
        "forecast_24h_geojson": res["forecast_24h_geojson"],
        "forecast_48h_geojson": res["forecast_48h_geojson"],
        "particles": res["particles"]
    }
