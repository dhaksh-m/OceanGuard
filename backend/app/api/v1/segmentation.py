from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.models.schemas import SegmentationResult
from ml.unet_model import OilSpillUNetPredictor

router = APIRouter()
predictor = OilSpillUNetPredictor()

@router.post("/predict", response_model=SegmentationResult)
def predict_oil_spill(incident_id: str = "INC-2026-0901", bbox: list = None):
    """
    Run UNet ML model segmentation on SAR scene tile to segment oil slick pixels,
    compute geometric metrics, and perform look-alike rejection.
    """
    if bbox is None:
        bbox = [103.81, 1.22, 103.95, 1.34]

    result = predictor.predict_mask(bbox=bbox)

    return {
        "incident_id": incident_id,
        "scene_id": "S1A_IW_GRDH_1SDV_20260902T141520",
        "mask_uri": f"s3://oceanguard-masks/{incident_id}/mask.tif",
        "confidence": result["sar_confidence"],
        "lookalike_score": result["lookalike_score"],
        "is_spill": result["is_spill"],
        "metrics": result["metrics"],
        "polygon_geojson": result["polygon_geojson"]
    }
