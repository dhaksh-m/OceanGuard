from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime

from app.models.schemas import Incident, IncidentCreate, IncidentUpdate
from app.services.mock_data import MOCK_INCIDENTS


router = APIRouter()


# -------------------------------------------------------------------
# Get all incidents
# -------------------------------------------------------------------

@router.get("", response_model=List[Incident])
def get_incidents(
    status_filter: Optional[str] = Query(
        None,
        alias="status"
    ),
    limit: int = 50
):
    """
    Retrieve list of active or archived oil spill incidents.
    """

    results = MOCK_INCIDENTS

    if status_filter:

        results = [
            inc
            for inc in results
            if inc["status"].upper()
            == status_filter.upper()
        ]

    return results[:limit]


# -------------------------------------------------------------------
# Get incident by ID
# -------------------------------------------------------------------

@router.get(
    "/{incident_id}",
    response_model=Incident
)
def get_incident_by_id(
    incident_id: str
):
    """
    Get detailed information for a specific incident.
    """

    for inc in MOCK_INCIDENTS:

        if (
            inc["id"].upper()
            == incident_id.upper()
            or
            inc["code"].upper()
            == incident_id.upper()
        ):
            return inc

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=(
            f"Incident with ID "
            f"'{incident_id}' not found."
        )
    )


# -------------------------------------------------------------------
# Create incident
# -------------------------------------------------------------------

@router.post(
    "",
    response_model=Incident,
    status_code=status.HTTP_201_CREATED
)
def create_incident(
    payload: IncidentCreate
):
    """
    Manually create or trigger an incident
    from scene detection.
    """

    new_id = (
        f"INC-2026-{len(MOCK_INCIDENTS) + 900}"
    )

    code = (
        f"OG-SPILL-{len(MOCK_INCIDENTS) + 900}"
    )

    new_incident = {

        "id":
            new_id,

        "code":
            code,

        "name":
            payload.name,

        "region":
            payload.region,

        "latitude":
            payload.latitude,

        "longitude":
            payload.longitude,

        "status":
            "DETECTED",

        "detected_at":
            datetime.utcnow().isoformat() + "Z",

        "slick_area_km2":
            12.8,

        "slick_perimeter_km":
            24.5,

        "sar_confidence":
            0.92,

        "lookalike_probability":
            0.08,

        "estimated_age_hours":
            4.0,

        # Use the real demo SAR scene when
        # no scene_id is provided.
        "scene_id":
            payload.scene_id
            or "dht_edelweiss_pass",

        "primary_vessel_of_interest_id":
            None
    }

    MOCK_INCIDENTS.append(
        new_incident
    )

    return new_incident


# -------------------------------------------------------------------
# Update incident
# -------------------------------------------------------------------

@router.patch(
    "/{incident_id}",
    response_model=Incident
)
def update_incident_status(
    incident_id: str,
    payload: IncidentUpdate
):
    """
    Update incident status or metadata.
    """

    for inc in MOCK_INCIDENTS:

        if (
            inc["id"].upper()
            == incident_id.upper()
        ):

            if payload.name:
                inc["name"] = payload.name

            if payload.status:
                inc["status"] = payload.status

            return inc

    raise HTTPException(
        status_code=404,
        detail="Incident not found"
    )