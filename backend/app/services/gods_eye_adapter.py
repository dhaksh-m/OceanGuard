"""
God's Eye View Adapter - mirrors core visual & data patterns from https://github.com/bilawalsidhu/gods-eye-view
Provides:
 - vessel iconOrientation logic (screen-space heading projection)
 - trail fading config
 - sensor style definitions (CRT, NVG, FLIR, Thermal, etc.)
 - HUD telemetry helpers
All logic is lightweight and safe to use both server & frontend.
"""
from typing import Dict, Any
import math

# God's Eye visual styles (1-7) - GLSL-style sensor looks
SENSOR_STYLES = {
    "normal": {"id": 1, "label": "Normal", "css_filter": "none", "glsl": "normal"},
    "crt": {"id": 2, "label": "CRT", "css_filter": "contrast(1.15) brightness(0.95) saturate(0.7) hue-rotate(5deg)", "glsl": "crt-scanline"},
    "nvg": {"id": 3, "label": "NVG", "css_filter": "brightness(1.2) contrast(1.25) hue-rotate(75deg) saturate(0.45) sepia(0.2)", "glsl": "nvg-green"},
    "thermal": {"id": 4, "label": "Thermal", "css_filter": "invert(0.85) hue-rotate(180deg) contrast(1.3) brightness(1.1)", "glsl": "thermal-ironbow"},
    "flir": {"id": 5, "label": "FLIR", "css_filter": "grayscale(1) invert(1) contrast(1.4) brightness(1.05)", "glsl": "flir-white-hot"},
    "noir": {"id": 6, "label": "Noir", "css_filter": "grayscale(1) contrast(1.2) brightness(0.9)", "glsl": "noir"},
    "snow": {"id": 7, "label": "Snow", "css_filter": "brightness(1.35) contrast(0.9) saturate(0.2) hue-rotate(10deg)", "glsl": "snow"},
}

def get_sensor_style(style_key: str) -> Dict[str, Any]:
    return SENSOR_STYLES.get(style_key.lower(), SENSOR_STYLES["normal"])

def compute_icon_orientation(heading_deg: float, map_bearing_deg: float = 0.0) -> float:
    """
    God's Eye world-stable icon: aircraft/ships point along true real-world heading at every camera angle.
    Equivalent to src/data/iconOrientation.js - per-frame screen-space course projection.
    Simplified: screen_heading = heading - map_bearing
    """
    return (heading_deg - map_bearing_deg) % 360.0

def horizon_cull(lat: float, lon: float, center_lat: float, center_lon: float, zoom: int = 12) -> bool:
    """
    God's Eye horizon cull: don't render vessels far beyond viewport.
    At zoom 12, ~15km radius; at zoom 5, larger.
    """
    # Approx distance
    dlat = (lat - center_lat) * 111.0
    dlon = (lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
    dist_km = math.hypot(dlat, dlon)
    max_km = 50 if zoom <= 8 else 25 if zoom <= 11 else 15
    return dist_km > max_km  # True = cull (hide)

def detection_box_for_vessel(vessel: Dict[str, Any], zoom: int = 12) -> Dict[str, Any]:
    """
    God's Eye detection overlay: screen-space bounding boxes + IDs on everything in view.
    Returns box meta for frontend to render.
    """
    return {
        "id": f"DET-{vessel.get('mmsi')}",
        "label": f"{vessel.get('name')} | {vessel.get('ship_type')}",
        "confidence": vessel.get("threat_score", vessel.get("sar_confidence", 75.0)) / 100.0,
        "class": "VESSEL",
        "heading_deg": vessel.get("heading_deg", 0),
        "world_stable": True
    }

def hud_telemetry_payload(active_incident: Dict[str, Any], live_vessels: list, segmentation: Dict[str, Any]) -> Dict[str, Any]:
    """
    God's Eye military HUD intelligence payload.
    """
    top_candidate = None
    if live_vessels:
        # sort by threat_score
        sorted_v = sorted(live_vessels, key=lambda x: x.get("threat_score", 0), reverse=True)
        top_candidate = sorted_v[0] if sorted_v else None
    return {
        "mode": "TACTICAL_HUD",
        "incident_code": active_incident.get("code") if active_incident else "NO_ACTIVE",
        "slick_confidence": round(segmentation.get("confidence", 0)*100, 1) if segmentation and segmentation.get("confidence") else None,
        "tracked_contacts": len(live_vessels),
        "primary_contact": top_candidate.get("name") if top_candidate else None,
        "sensor": "SAR-VV+VH | AIS-L",
        "timestamp": active_incident.get("detected_at") if active_incident else None
    }
