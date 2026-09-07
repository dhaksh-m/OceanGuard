from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import SatelliteScene
from app.services.mock_data import MOCK_SATELLITE_SCENES


router = APIRouter()


# -------------------------------------------------------------------
# Project paths
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]


SAR_SCENES_DIR = (
    PROJECT_ROOT
    / "SIH2026"
    / "assets"
    / "sar_samples"
    / "scenes"
)


# -------------------------------------------------------------------
# List satellite scenes
# -------------------------------------------------------------------

@router.get(
    "/scenes",
    response_model=List[SatelliteScene]
)
def list_satellite_scenes():
    """
    List ingested Sentinel-1 SAR satellite scenes.
    """

    return MOCK_SATELLITE_SCENES


# -------------------------------------------------------------------
# Get satellite scene
# -------------------------------------------------------------------

@router.get(
    "/scenes/{scene_id}",
    response_model=SatelliteScene
)
def get_satellite_scene(scene_id: str):
    """
    Get metadata for a specific Sentinel-1 scene.
    """

    for scene in MOCK_SATELLITE_SCENES:

        if (
            scene["id"].upper()
            == scene_id.upper()
            or
            scene["scene_id"].upper()
            == scene_id.upper()
        ):

            return scene

    raise HTTPException(
        status_code=404,
        detail="Satellite scene not found"
    )


# -------------------------------------------------------------------
# Ingest satellite scene
# -------------------------------------------------------------------

@router.post(
    "/scenes/ingest",
    response_model=SatelliteScene,
    status_code=status.HTTP_202_ACCEPTED
)
def trigger_scene_ingestion(
    scene_id: str = "dht_edelweiss_pass"
):
    """
    Simulate Sentinel-1 SAR scene discovery and ingestion.

    For local development, the ingested scene is connected
    to the actual SAR image stored in the repository.
    """

    # ---------------------------------------------------------------
    # Find actual SAR image
    # ---------------------------------------------------------------

    possible_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
    ]

    image_path = None

    for extension in possible_extensions:

        candidate = (
            SAR_SCENES_DIR
            / f"{scene_id}{extension}"
        )

        if candidate.exists():

            image_path = candidate
            break

    if image_path is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"SAR image for scene "
                f"'{scene_id}' was not found "
                f"in {SAR_SCENES_DIR}"
            )
        )

    # ---------------------------------------------------------------
    # Check if scene already exists
    # ---------------------------------------------------------------

    for scene in MOCK_SATELLITE_SCENES:

        if (
            scene["scene_id"].upper()
            == scene_id.upper()
        ):

            # Update existing scene with real image path
            scene["storage_uri"] = str(
                image_path
            )

            scene["processing_status"] = "COMPLETED"

            return scene

    # ---------------------------------------------------------------
    # Create new scene
    # ---------------------------------------------------------------

    new_scene = {

        "id":
            f"SCENE-00{len(MOCK_SATELLITE_SCENES) + 1}",

        "scene_id":
            scene_id,

        "platform":
            "Sentinel-1A",

        "mode":
            "IW",

        "polarization":
            "VV+VH",

        "acquisition_time":
            "2026-09-02T16:00:00Z",

        "pass_direction":
            "ASCENDING",

        "spatial_resolution_m":
            10.0,

        "bbox": [
            103.81,
            1.22,
            103.95,
            1.34
        ],

        "processing_status":
            "COMPLETED",

        "storage_uri":
            str(image_path)
    }

    MOCK_SATELLITE_SCENES.append(
        new_scene
    )

    return new_scene