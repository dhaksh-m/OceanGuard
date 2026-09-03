from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IncidentBase(BaseModel):
    name: str
    region: str
    latitude: float
    longitude: float

class IncidentCreate(IncidentBase):
    scene_id: Optional[str] = None

class IncidentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class Incident(IncidentBase):
    id: str
    code: str
    status: str  # DETECTED, PROCESSING, VALIDATED, ORIGIN_ANALYSIS, VESSEL_CORRELATION, INVESTIGATION, RESOLVED, DISMISSED
    detected_at: datetime
    slick_area_km2: float
    slick_perimeter_km: float
    sar_confidence: float
    lookalike_probability: float
    estimated_age_hours: float
    scene_id: str
    primary_vessel_of_interest_id: Optional[str] = None

    model_config = {"from_attributes": True}

class SatelliteScene(BaseModel):
    id: str
    scene_id: str
    platform: str
    mode: str
    polarization: str
    acquisition_time: datetime
    pass_direction: str
    spatial_resolution_m: float
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat]
    processing_status: str
    storage_uri: str

class SpillGeometryMetrics(BaseModel):
    area_km2: float
    perimeter_km: float
    centroid_lat: float
    centroid_lon: float
    bbox: List[float]
    major_axis_km: float
    minor_axis_km: float
    orientation_deg: float
    compactness: float

class SegmentationResult(BaseModel):
    incident_id: str
    scene_id: str
    mask_uri: str
    confidence: float
    lookalike_score: float
    is_spill: bool
    metrics: SpillGeometryMetrics
    polygon_geojson: Dict[str, Any]

class DriftParticle(BaseModel):
    particle_id: int
    timestamp: datetime
    lat: float
    lon: float
    probability: float

class OceanDriftResult(BaseModel):
    incident_id: str
    simulated_at: datetime
    wind_speed_knots: float
    wind_direction_deg: float
    current_speed_knots: float
    current_direction_deg: float
    origin_zone_geojson: Dict[str, Any]
    forecast_24h_geojson: Dict[str, Any]
    forecast_48h_geojson: Dict[str, Any]
    particles: List[DriftParticle]

class Vessel(BaseModel):
    id: str
    mmsi: int
    imo: Optional[int] = None
    name: str
    ship_type: str
    flag: str
    length_m: float
    breadth_m: float
    callsign: Optional[str] = None
    status: str

class AISPosition(BaseModel):
    id: str
    vessel_id: str
    mmsi: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed_knots: float
    course_deg: float
    heading_deg: float
    nav_status: str

class AttributionScore(BaseModel):
    id: str
    spill_id: str
    vessel_id: str
    vessel_name: str
    mmsi: int
    overall_score: float  # 0.0 - 100.0
    spatial_score: float  # 25% weight
    temporal_score: float # 20% weight
    trajectory_score: float # 20% weight
    speed_score: float   # 10% weight
    heading_score: float # 10% weight
    ais_anomaly_score: float # 10% weight
    vessel_context_score: float # 5% weight
    category: str # 'Candidate Vessel', 'Vessel of Interest'
    confidence_level: str # CRITICAL, HIGH, MODERATE, LOW
    explanation: Dict[str, Any]

class EvidenceItem(BaseModel):
    id: str
    incident_id: str
    title: str
    category: str
    description: str
    created_at: datetime
    file_url: Optional[str] = None
    metadata_json: Dict[str, Any]

class IncidentReport(BaseModel):
    report_id: str
    incident_id: str
    incident_name: str
    generated_at: datetime
    summary: str
    detected_at: str
    location_formatted: str
    slick_area_km2: float
    confidence_score: float
    top_candidates: List[AttributionScore]
    environmental_conditions: Dict[str, Any]
    download_urls: Dict[str, str]
