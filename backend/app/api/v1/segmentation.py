from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import SegmentationResult
from app.services.mock_data import (
    MOCK_INCIDENTS,
    MOCK_SATELLITE_SCENES,
)

from ml.unet_model import OilSpillUNetPredictor


router = APIRouter()


# -------------------------------------------------------------------
# Load the trained POSEatSea model once
# -------------------------------------------------------------------

predictor = OilSpillUNetPredictor()


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


MASK_ROOT = (
    PROJECT_ROOT
    / "backend"
    / "data"
    / "masks"
)


# -------------------------------------------------------------------
# Request schema
# -------------------------------------------------------------------

class SegmentationRequest(BaseModel):
    incident_id: str
    bbox: Optional[list[float]] = None


# -------------------------------------------------------------------
# Find incident
# -------------------------------------------------------------------

def find_incident(incident_id: str):

    for incident in MOCK_INCIDENTS:

        if (
            incident["id"].upper()
            == incident_id.upper()
        ):
            return incident

        if (
            incident.get("code", "").upper()
            == incident_id.upper()
        ):
            return incident

    return None


# -------------------------------------------------------------------
# Find satellite scene
# -------------------------------------------------------------------

def find_scene(scene_id: str):

    for scene in MOCK_SATELLITE_SCENES:

        if (
            scene["id"].upper()
            == scene_id.upper()
            or
            scene["scene_id"].upper()
            == scene_id.upper()
        ):

            return scene

    return None


# -------------------------------------------------------------------
# Resolve actual SAR image
# -------------------------------------------------------------------

def resolve_sar_image(scene: dict) -> Path:

    storage_uri = scene.get("storage_uri")

    # ---------------------------------------------------------------
    # First try the storage URI if it is a real local path
    # ---------------------------------------------------------------

    if storage_uri:
        # local://filename is a logical URI used by the demo data.
        # Resolve it against the repository SAR scene directory.
        if storage_uri.startswith("local://"):
            local_name = storage_uri[len("local://"):]
            local_path = SAR_SCENES_DIR / local_name
        else:
            local_path = Path(storage_uri)

        if local_path.exists():
            return local_path

    # ---------------------------------------------------------------
    # If storage_uri is an old/mock S3 URI, resolve the scene
    # against the local SAR samples directory.
    # ---------------------------------------------------------------

    scene_id = scene.get("scene_id", "")

    possible_files = [
        SAR_SCENES_DIR / f"{scene_id}.jpg",
        SAR_SCENES_DIR / f"{scene_id}.jpeg",
        SAR_SCENES_DIR / f"{scene_id}.png",
        SAR_SCENES_DIR / f"{scene_id}.tif",
        SAR_SCENES_DIR / f"{scene_id}.tiff",
    ]

    for image_path in possible_files:

        if image_path.exists():

            return image_path

    # ---------------------------------------------------------------
    # Known local demo scenes
    # ---------------------------------------------------------------

    known_demo_images = {
        "WAKASHIO_REEF": "wakashio_reef.jpg",
        "KOTA_SURIA_PASS": "kota_suria_pass.jpg",
        "DHT_EDELWEISS_PASS": "dht_edelweiss_pass.jpg",
        "VERY_MARIA_PASS": "very_maria_pass.jpg",
        "PALONA_PASS": "palona_pass.jpg",
        "S1A_IW_20260902": "dht_edelweiss_pass.jpg",
        "S1A_IW_GRDH_20260902_DEMO": "dht_edelweiss_pass.jpg",
    }

    known_filename = known_demo_images.get(scene_id.upper())
    if known_filename:
        demo_image = SAR_SCENES_DIR / known_filename
        if demo_image.exists():
            return demo_image

    # ---------------------------------------------------------------
    # Nothing found
    # ---------------------------------------------------------------

    raise HTTPException(
        status_code=404,
        detail=(
            f"SAR image not found for scene "
            f"'{scene_id}'. "
            f"Checked storage URI '{storage_uri}' "
            f"and local SAR scene directory "
            f"'{SAR_SCENES_DIR}'."
        ),
    )


# -------------------------------------------------------------------
# Prediction endpoint
# -------------------------------------------------------------------

@router.post(
    "/predict",
    response_model=SegmentationResult,
)
def predict_oil_spill(
    request: SegmentationRequest,
):

    # ---------------------------------------------------------------
    # 1. Find incident
    # ---------------------------------------------------------------

    incident = find_incident(
        request.incident_id
    )

    if incident is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Incident '{request.incident_id}' "
                f"not found."
            ),
        )

    # ---------------------------------------------------------------
    # 2. Get scene ID from incident
    # ---------------------------------------------------------------

    scene_id = incident.get("scene_id")

    if not scene_id:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Incident '{request.incident_id}' "
                f"does not have a scene_id."
            ),
        )

    # ---------------------------------------------------------------
    # 3. Find satellite scene
    # ---------------------------------------------------------------

    scene = find_scene(scene_id)

    if scene is None:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Satellite scene '{scene_id}' "
                f"not found."
            ),
        )

    # ---------------------------------------------------------------
    # 4. Resolve actual SAR image
    # ---------------------------------------------------------------

    sar_image_path = resolve_sar_image(scene)

    # ---------------------------------------------------------------
    # 5. Determine bounding box
    # ---------------------------------------------------------------

    bbox = request.bbox

    if bbox is None:

        bbox = scene.get("bbox")

    if bbox is None:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Scene '{scene_id}' "
                f"does not have a geographic bbox."
            ),
        )

    # ---------------------------------------------------------------
    # Validate bbox
    # ---------------------------------------------------------------

    if len(bbox) != 4:

        raise HTTPException(
            status_code=400,
            detail=(
                "bbox must contain exactly "
                "4 values: "
                "[min_lon, min_lat, max_lon, max_lat]"
            ),
        )

    # ---------------------------------------------------------------
    # 6. Run real ML model
    # ---------------------------------------------------------------

    try:

        result = predictor.predict_mask(
            sar_image_path=str(
                sar_image_path
            ),
            bbox=bbox,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"ML inference failed: "
                f"{str(e)}"
            ),
        )

    # ---------------------------------------------------------------
    # 7. Save prediction mask
    # ---------------------------------------------------------------

    incident_mask_dir = (
        MASK_ROOT
        / request.incident_id
    )

    incident_mask_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    mask_path = (
        incident_mask_dir
        / "mask.tif"
    )

    try:

        predictor.save_mask(
            result["mask"],
            str(mask_path),
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save prediction mask: "
                f"{str(e)}"
            ),
        )

    # ---------------------------------------------------------------
    # 8. Return result
    # ---------------------------------------------------------------

    return {

        "incident_id":
            request.incident_id,

        "scene_id":
            scene_id,

        "mask_uri":
            str(mask_path),

        "confidence":
            result["sar_confidence"],

        "lookalike_score":
            result["lookalike_score"],

        "is_spill":
            result["is_spill"],

        "metrics":
            result["metrics"],

        "polygon_geojson":
            result["polygon_geojson"],
    }