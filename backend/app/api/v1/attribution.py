from fastapi import APIRouter
from typing import List
from app.models.schemas import AttributionScore
from app.services.mock_data import MOCK_VESSELS
from attribution.scorer import ExplainableAttributionScorer
from ais.anomaly_detector import AISAnomalyDetector

router = APIRouter()
scorer = ExplainableAttributionScorer()

@router.post("/calculate", response_model=List[AttributionScore])
def calculate_attribution(incident_id: str = "INC-2026-0901"):
    """
    Computes explainable vessel attribution scores for all candidate vessels relative to the probable origin zone.
    Returns ranked candidates without declaring legal guilt.
    """
    results = []
    
    # Custom spatio-temporal inputs per mock candidate vessel
    vessel_params = [
        {
            "vessel": MOCK_VESSELS[0], # PACIFIC EXPLORER
            "dist": 1.2,
            "t_delta": 0.4,
            "traj_angle": 12.0,
            "speed": 5.2,
            "heading": 68.0,
            "anomaly": {"has_speed_anomaly": True, "has_ais_gap": False, "max_gap_minutes": 12.0}
        },
        {
            "vessel": MOCK_VESSELS[1], # OCEAN GEMINI
            "dist": 4.8,
            "t_delta": 1.5,
            "traj_angle": 28.0,
            "speed": 12.4,
            "heading": 72.0,
            "anomaly": {"has_speed_anomaly": False, "has_ais_gap": True, "max_gap_minutes": 52.0}
        },
        {
            "vessel": MOCK_VESSELS[2], # EVER PRIDE
            "dist": 9.5,
            "t_delta": 3.2,
            "traj_angle": 45.0,
            "speed": 18.5,
            "heading": 85.0,
            "anomaly": {"has_speed_anomaly": False, "has_ais_gap": False, "max_gap_minutes": 5.0}
        },
        {
            "vessel": MOCK_VESSELS[3], # NORTH SEA VOYAGER
            "dist": 16.2,
            "t_delta": 4.8,
            "traj_angle": 62.0,
            "speed": 14.1,
            "heading": 90.0,
            "anomaly": {"has_speed_anomaly": False, "has_ais_gap": False, "max_gap_minutes": 2.0}
        }
    ]

    for p in vessel_params:
        sc = scorer.calculate_score(
            vessel=p["vessel"],
            distance_to_origin_km=p["dist"],
            time_delta_hours=p["t_delta"],
            trajectory_angle_diff_deg=p["traj_angle"],
            speed_knots=p["speed"],
            heading_deg=p["heading"],
            slick_orientation_deg=65.0,
            anomaly_data=p["anomaly"]
        )
        res = {
            "id": f"ATTR-{p['vessel']['id']}",
            "spill_id": incident_id,
            **sc
        }
        results.append(res)

    # Sort descending by overall score
    results.sort(key=lambda x: x["overall_score"], reverse=True)
    return results
