from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from typing import Dict, Any, Optional
from app.models.schemas import SegmentationResult
from ml.unet_model import OilSpillUNetPredictor
import numpy as np
from PIL import Image
import io

router = APIRouter()
predictor = OilSpillUNetPredictor()

@router.post("/predict", response_model=SegmentationResult)
def predict_oil_spill(incident_id: str = "INC-2026-0901", bbox: list = None):
    """
    Run UNet ML model segmentation on SAR scene tile to segment oil slick pixels,
    compute geometric metrics, and perform look-alike rejection.
    Ocean-only guarantee: results on land are suppressed via land_mask.
    """
    if bbox is None:
        bbox = [103.81, 1.22, 103.95, 1.34]

    result = predictor.predict_mask(bbox=bbox)

    # Ocean-only gate: if predictor says not valid ocean spill, return suppressed metrics
    if not result.get("is_valid_ocean_spill", True):
        # Still return structure but mark is_spill False and polygon null
        return {
            "incident_id": incident_id,
            "scene_id": "S1A_IW_GRDH_1SDV_20260902T141520",
            "mask_uri": f"s3://oceanguard-masks/{incident_id}/mask.tif",
            "confidence": 0.0,
            "lookalike_score": result.get("lookalike_score", 0.95),
            "is_spill": False,
            "metrics": result["metrics"],
            "polygon_geojson": None,
            "water_ratio": result.get("water_ratio", 0.0),
            "land_mask_provenance": result.get("land_mask_provenance")
        }

    return {
        "incident_id": incident_id,
        "scene_id": "S1A_IW_GRDH_1SDV_20260902T141520",
        "mask_uri": f"s3://oceanguard-masks/{incident_id}/mask.tif",
        "confidence": result["sar_confidence"],
        "lookalike_score": result["lookalike_score"],
        "is_spill": result["is_spill"],
        "metrics": result["metrics"],
        "polygon_geojson": result["polygon_geojson"],
        "water_ratio": result.get("water_ratio", 1.0),
        "land_mask_provenance": result.get("land_mask_provenance")
    }

@router.post("/predict/upload")
def predict_from_upload(
    incident_id: str = "INC-2026-0901",
    bbox: Optional[str] = Query(None, description=" bbox as comma separated min_lon,min_lat,max_lon,max_lat"),
    file: UploadFile = File(...)
):
    """
    Upload a SAR chip (JPEG/PNG/TIF, 400x400 recommended) and run real UNet inference.
    Land masking is enforced.
    """
    try:
        contents = file.file.read()
        pil = Image.open(io.BytesIO(contents)).convert("L")
        arr = np.array(pil)
        bbox_list = None
        if bbox:
            try:
                bbox_list = [float(x) for x in bbox.split(",")]
            except Exception:
                bbox_list = [103.81, 1.22, 103.95, 1.34]
        result = predictor.predict_mask(sar_image_data=arr, bbox=bbox_list)
        if not result.get("is_valid_ocean_spill", True):
            return {
                "incident_id": incident_id,
                "is_spill": False,
                "rejection_reason": result.get("rejection_reason"),
                "water_ratio": result.get("water_ratio"),
                "land_mask_provenance": result.get("land_mask_provenance"),
                "metrics": result["metrics"]
            }
        return {
            "incident_id": incident_id,
            "is_spill": result["is_spill"],
            "confidence": result["sar_confidence"],
            "lookalike_score": result["lookalike_score"],
            "metrics": result["metrics"],
            "polygon_geojson": result["polygon_geojson"],
            "water_ratio": result.get("water_ratio"),
            "model_version": result.get("model_version"),
            "synthetic_fallback": result.get("synthetic_fallback")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAR upload inference failed: {e}")

@router.get("/model/info")
def get_model_info():
    """Returns ML model provenance and land-mask status."""
    return {
        "model_version": predictor.model_version,
        "threshold": predictor.threshold,
        "synthetic_mode": predictor.synthetic_mode,
        "land_mask": "OSM-coastline-simplified + MIN_WATER_RATIO 0.80",
        "ocean_only_guarantee": True,
        "checkpoint_exists": predictor.checkpoint_path.exists() if hasattr(predictor, 'checkpoint_path') else False
    }
