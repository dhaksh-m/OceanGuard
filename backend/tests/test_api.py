import pytest
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "OceanGuard"
    assert data["status"] == "ONLINE"

def test_system_health():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "services" in data

def test_get_incidents():
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_incident_by_id():
    response = client.get("/api/v1/incidents/INC-2026-0901")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "INC-2026-0901"

def test_create_and_update_incident():
    create_payload = {
        "name": "Test Offshore Spill Incident",
        "region": "North Sea Sector 4",
        "latitude": 56.2,
        "longitude": 3.4
    }
    response = client.post("/api/v1/incidents", json=create_payload)
    assert response.status_code == 201
    created = response.json()
    inc_id = created["id"]
    
    # Update status
    update_response = client.patch(f"/api/v1/incidents/{inc_id}", json={"status": "INVESTIGATION"})
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "INVESTIGATION"

def test_satellite_scenes():
    response = client.get("/api/v1/satellite/scenes")
    assert response.status_code == 200
    assert len(response.json()) > 0

    ingest_resp = client.post("/api/v1/satellite/scenes/ingest?scene_id=TEST_S1A_SCENE")
    assert ingest_resp.status_code == 202
    assert ingest_resp.json()["scene_id"] == "TEST_S1A_SCENE"

def test_segmentation_prediction():
    response = client.post("/api/v1/segmentation/predict", json={"incident_id": "INC-2026-0901"})
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "polygon_geojson" in data
    assert data["confidence"] > 0.5

def test_ocean_drift_simulation():
    response = client.post("/api/v1/ocean/drift", json={"incident_id": "INC-2026-0901", "lat": 1.312, "lon": 103.854})
    assert response.status_code == 200
    data = response.json()
    assert "origin_zone_geojson" in data
    assert "forecast_24h_geojson" in data
    assert "forecast_48h_geojson" in data
    assert len(data["particles"]) > 0

def test_ais_vessels_and_tracks():
    vessels_resp = client.get("/api/v1/ais/vessels")
    assert vessels_resp.status_code == 200
    vessels = vessels_resp.json()
    assert len(vessels) > 0

    track_resp = client.get(f"/api/v1/ais/vessels/{vessels[0]['id']}/track")
    assert track_resp.status_code == 200
    assert "track_points" in track_resp.json()

def test_attribution_calculation():
    response = client.post("/api/v1/attribution/calculate", json={"incident_id": "INC-2026-0901"})
    assert response.status_code == 200
    candidates = response.json()
    assert len(candidates) > 0
    top_candidate = candidates[0]
    assert "overall_score" in top_candidate
    assert "explanation" in top_candidate
    assert top_candidate["category"] in ["Vessel of Interest", "Candidate Vessel"]

def test_reports_generation():
    html_resp = client.get("/api/v1/reports/INC-2026-0901/html")
    assert html_resp.status_code == 200
    assert "OceanGuard Maritime Incident Evidence Report" in html_resp.text

    json_resp = client.get("/api/v1/reports/INC-2026-0901/json")
    assert json_resp.status_code == 200
    assert json_resp.json()["report_id"] == "REP-INC-2026-0901"

def test_evidence_locker():
    get_resp = client.get("/api/v1/evidence/INC-2026-0901")
    assert get_resp.status_code == 200
    assert isinstance(get_resp.json(), list)

    post_resp = client.post(
        "/api/v1/evidence/INC-2026-0901?title=Test%20Evidence&category=SAR_RASTER&description=Test%20desc"
    )
    assert post_resp.status_code == 201
