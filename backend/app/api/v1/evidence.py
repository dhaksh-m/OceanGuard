from fastapi import APIRouter
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()

MOCK_EVIDENCE_ITEMS = [
    {
        "id": "EV-001",
        "incident_id": "INC-2026-0901",
        "title": "Sentinel-1A SAR VV Amplitude Raster Tile",
        "category": "SAR_RASTER",
        "description": "PreprocessedVV polarized SAR backscatter tile showing low-backscatter oil slick dark patch.",
        "created_at": "2026-09-02T14:20:00Z",
        "file_url": "s3://oceanguard-evidence/INC-2026-0901/sar_vv_tile.png",
        "metadata_json": {"resolution_m": 10.0, "polarization": "VV", "incidence_angle_deg": 38.4}
    },
    {
        "id": "EV-002",
        "incident_id": "INC-2026-0901",
        "title": "AIS High-Frequency Position Logs (PACIFIC EXPLORER)",
        "category": "AIS_LOG",
        "description": "Normalized NMEA AIS position stream showing speed reduction from 14.1 kts to 5.2 kts near origin zone.",
        "created_at": "2026-09-02T14:35:00Z",
        "file_url": "s3://oceanguard-evidence/INC-2026-0901/ais_mmsi_636018432.json",
        "metadata_json": {"mmsi": 636018432, "points_count": 142, "speed_drop_detected": True}
    },
    {
        "id": "EV-003",
        "incident_id": "INC-2026-0901",
        "title": "Copernicus Surface Current Vector Field",
        "category": "WEATHER_DATA",
        "description": "Copernicus Marine physical oceanography surface flow (0.92 m/s @ 65°).",
        "created_at": "2026-09-02T14:25:00Z",
        "file_url": "s3://oceanguard-evidence/INC-2026-0901/ocean_currents.nc",
        "metadata_json": {"provider": "Copernicus Marine", "u_ms": 0.83, "v_ms": 0.38}
    }
]

@router.get("/{incident_id}", response_model=List[Dict[str, Any]])
def get_incident_evidence(incident_id: str):
    """
    Retrieve chain-of-custody evidence items logged for an incident.
    """
    items = [ev for ev in MOCK_EVIDENCE_ITEMS if ev["incident_id"].upper() == incident_id.upper()]
    if not items:
        return MOCK_EVIDENCE_ITEMS # Return default set if new ID
    return items

@router.post("/{incident_id}", status_code=201)
def add_evidence_item(incident_id: str, title: str, category: str, description: str):
    """
    Log new evidence artifact into the evidence locker.
    """
    item = {
        "id": f"EV-00{len(MOCK_EVIDENCE_ITEMS) + 1}",
        "incident_id": incident_id,
        "title": title,
        "category": category,
        "description": description,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "file_url": f"s3://oceanguard-evidence/{incident_id}/{category.lower()}_artifact.dat",
        "metadata_json": {"analyst_action": "Manual evidence attachment"}
    }
    MOCK_EVIDENCE_ITEMS.append(item)
    return item
