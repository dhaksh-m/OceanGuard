from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.schemas import SatelliteScene
from app.services.mock_data import MOCK_SATELLITE_SCENES

router = APIRouter()

@router.get("/scenes", response_model=List[SatelliteScene])
def list_satellite_scenes():
    """
    List ingested Sentinel-1 SAR satellite scenes.
    """
    return MOCK_SATELLITE_SCENES

@router.get("/scenes/{scene_id}", response_model=SatelliteScene)
def get_satellite_scene(scene_id: str):
    """
    Get metadata for a specific Sentinel-1 scene.
    """
    for sc in MOCK_SATELLITE_SCENES:
        if sc["id"].upper() == scene_id.upper() or sc["scene_id"].upper() == scene_id.upper():
            return sc
    raise HTTPException(status_code=404, detail="Satellite scene not found")

@router.post("/scenes/ingest", response_model=SatelliteScene, status_code=status.HTTP_202_ACCEPTED)
def trigger_scene_ingestion(scene_id: str = "S1A_IW_GRDH_20260902_DEMO"):
    """
    Triggers automated Sentinel-1 SAR scene discovery, preprocessing & calibration pipeline.
    """
    new_scene = {
        "id": f"SCENE-00{len(MOCK_SATELLITE_SCENES) + 1}",
        "scene_id": scene_id,
        "platform": "Sentinel-1A",
        "mode": "IW",
        "polarization": "VV+VH",
        "acquisition_time": "2026-09-02T16:00:00Z",
        "pass_direction": "ASCENDING",
        "spatial_resolution_m": 10.0,
        "bbox": [103.75, 1.18, 104.10, 1.42],
        "processing_status": "COMPLETED",
        "storage_uri": f"s3://oceanguard-scenes/2026/09/02/{scene_id}.tif"
    }
    MOCK_SATELLITE_SCENES.append(new_scene)
    return new_scene
