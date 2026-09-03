from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.mock_data import MOCK_INCIDENTS, MOCK_VESSELS
from ml.unet_model import OilSpillUNetPredictor
from ocean.drift_simulation import OceanDriftEngine
from attribution.scorer import ExplainableAttributionScorer
from reports.generator import IncidentReportGenerator

router = APIRouter()

@router.get("/{incident_id}/html", response_class=HTMLResponse)
def get_incident_html_report(incident_id: str):
    """
    Generate and render complete HTML Incident Investigation Report.
    """
    incident = None
    for inc in MOCK_INCIDENTS:
        if inc["id"].upper() == incident_id.upper():
            incident = inc
            break
    if not incident:
        incident = MOCK_INCIDENTS[0]

    predictor = OilSpillUNetPredictor()
    segmentation = predictor.predict_mask()
    drift = OceanDriftEngine().run_simulation(slick_centroid=(incident["latitude"], incident["longitude"]))
    
    scorer = ExplainableAttributionScorer()
    candidates = [
        scorer.calculate_score(MOCK_VESSELS[0], 1.2, 0.4, 12.0, 5.2, 68.0, 65.0, {"has_speed_anomaly": True}),
        scorer.calculate_score(MOCK_VESSELS[1], 4.8, 1.5, 28.0, 12.4, 72.0, 65.0, {"has_ais_gap": True})
    ]

    html_content = IncidentReportGenerator.generate_html_report(incident, segmentation, drift, candidates)
    return HTMLResponse(content=html_content)

@router.get("/{incident_id}/json")
def get_incident_json_report(incident_id: str):
    """
    Get structured JSON evidence report payload for API / export.
    """
    incident = None
    for inc in MOCK_INCIDENTS:
        if inc["id"].upper() == incident_id.upper():
            incident = inc
            break
    if not incident:
        incident = MOCK_INCIDENTS[0]

    return {
        "report_id": f"REP-{incident['id']}",
        "incident": incident,
        "generated_at": incident["detected_at"],
        "provenance": {
            "satellite_sensor": "Sentinel-1A SAR C-Band",
            "model_version": "U-Net OilSpillSeg v1.4.2",
            "drift_model": "OceanParcels Lagrangian 2D"
        }
    }
