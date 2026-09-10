from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.schemas import Vessel
from app.services.mock_data import MOCK_VESSELS
from app.services.ais_connector import get_live_ais_feed, get_vessel_trail
from app.services.gods_eye_adapter import SENSOR_STYLES

router = APIRouter()

@router.get("/vessels", response_model=List[Vessel])
def list_vessels():
    """
    List all active vessels monitored in the spatio-temporal boundary.
    """
    return MOCK_VESSELS

@router.get("/live")
def get_live_vessel_positions(
    min_lon: Optional[float] = Query(None, description="BBox min_lon for viewport-bounded filtering (God's Eye)"),
    min_lat: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None)
):
    """
    Get real-time open AIS stream position fixes for all monitored maritime vessels on the sea.
    - God's Eye viewport-bounded: optional bbox filters vessels to viewport.
    - Ocean-only: land vessels are automatically suppressed.
    - Includes trail & world_stable_heading for smooth motion.
    """
    bbox = None
    if None not in (min_lon, min_lat, max_lon, max_lat):
        bbox = [min_lon, min_lat, max_lon, max_lat]
    return get_live_ais_feed(bbox=bbox)

@router.get("/live/stream-info")
def get_stream_info():
    """God's Eye stream provenance & controls."""
    return {
        "source": "AISStream.io + Simulated Fleet (fallback)",
        "mode": "Server-side proxy (keys hidden from browser) + request budget 30/min",
        "ocean_filtered": True,
        "motion_model": "God's Eye 1-interval-behind + dead_reckoning lerp",
        "sensor_styles": list(SENSOR_STYLES.keys()),
        "trail_enabled": True
    }

@router.get("/vessels/{vessel_id}", response_model=Vessel)
def get_vessel_by_id(vessel_id: str):
    """
    Get detailed profile of a candidate vessel.
    """
    for v in MOCK_VESSELS:
        if v["id"].upper() == vessel_id.upper() or str(v["mmsi"]) == vessel_id:
            return v
    raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found.")

@router.get("/trail/{mmsi}")
def get_trail(mmsi: int):
    """God's Eye fading trail for a vessel."""
    trail = get_vessel_trail(mmsi)
    return {"mmsi": mmsi, "trail": trail, "count": len(trail)}

@router.get("/vessels/{vessel_id}/track")
def get_vessel_track(vessel_id: str):
    """
    Get spatio-temporal trajectory track points for a vessel.
    Uses real trail history if available, else synthetic.
    """
    vessel = None
    for v in MOCK_VESSELS:
        if v["id"].upper() == vessel_id.upper() or str(v["mmsi"]) == vessel_id:
            vessel = v
            break
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")

    # Try real trail
    try:
        mmsi = vessel["mmsi"]
        trail = get_vessel_trail(mmsi)
        if trail and len(trail) >= 4:
            # Convert to track_points format
            track_points = []
            for idx, tp in enumerate(trail[-12:]):
                track_points.append({
                    "timestamp": tp.get("ts"),
                    "lat": tp["lat"],
                    "lon": tp["lon"],
                    "speed_knots": 5.2 if vessel["id"] == "VESSEL-001" else 12.8,
                    "heading_deg": 68.0,
                    "course_deg": 65.0,
                    "nav_status": "UNDERWAY_USING_ENGINE"
                })
            return {
                "vessel_id": vessel["id"],
                "name": vessel["name"],
                "mmsi": vessel["mmsi"],
                "track_points": track_points,
                "source": "live_trail"
            }
    except Exception:
        pass

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
        "track_points": track_points,
        "source": "synthetic"
    }
