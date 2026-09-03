from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.models.schemas import Vessel
from app.services.mock_data import MOCK_VESSELS
from app.services.ais_connector import get_live_ais_feed

router = APIRouter()

@router.get("/vessels", response_model=List[Vessel])
def list_vessels():
    """
    List all active vessels monitored in the spatio-temporal boundary.
    """
    return MOCK_VESSELS

@router.get("/live")
def get_live_vessel_positions():
    """
    Get real-time open AIS stream position fixes for all monitored maritime vessels on the sea.
    """
    return get_live_ais_feed()

@router.get("/vessels/{vessel_id}", response_model=Vessel)
def get_vessel_by_id(vessel_id: str):
    """
    Get detailed profile of a candidate vessel.
    """
    for v in MOCK_VESSELS:
        if v["id"].upper() == vessel_id.upper() or str(v["mmsi"]) == vessel_id:
            return v
    raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found.")

@router.get("/vessels/{vessel_id}/track")
def get_vessel_track(vessel_id: str):
    """
    Get spatio-temporal trajectory track points for a vessel.
    """
    vessel = None
    for v in MOCK_VESSELS:
        if v["id"].upper() == vessel_id.upper() or str(v["mmsi"]) == vessel_id:
            vessel = v
            break
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    now = datetime.utcnow()
    base_lat = 1.2500
    base_lon = 103.7500
    track_points = []
    for i in range(12):
        t = now - timedelta(hours=12 - i)
        lat = base_lat + (i * 0.012) + (0.002 * (1 if i % 2 == 0 else -1))
        lon = base_lon + (i * 0.018)
        speed = 5.2 if (vessel["id"] == "VESSEL-001" and 5 <= i <= 7) else 13.8
        track_points.append({
            "timestamp": t.isoformat() + "Z",
            "lat": round(lat, 5),
            "lon": round(lon, 5),
            "speed_knots": speed,
            "heading_deg": 68.0,
            "course_deg": 65.0,
            "nav_status": "UNDERWAY_USING_ENGINE"
        })

    return {
        "vessel_id": vessel["id"],
        "name": vessel["name"],
        "mmsi": vessel["mmsi"],
        "track_points": track_points
    }
