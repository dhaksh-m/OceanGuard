from datetime import datetime, timedelta


# ============================================================
# MOCK INCIDENTS
# ============================================================

MOCK_INCIDENTS = [
    {
        "id": "INC-2026-0901",
        "code": "OG-SPILL-0901",
        "name": "Strait of Malacca Slick Alpha",
        "region": "Strait of Malacca (Eastbound Lane)",
        "latitude": 1.3120,
        "longitude": 103.8540,
        "status": "VESSEL_CORRELATION",
        "detected_at": "2026-09-02T14:15:00Z",
        "slick_area_km2": 15.42,
        "slick_perimeter_km": 29.8,
        "sar_confidence": 0.94,
        "lookalike_probability": 0.06,
        "estimated_age_hours": 5.5,

        # Real local SAR image
        "scene_id": "wakashio_reef",

        "primary_vessel_of_interest_id": "VESSEL-001",
    },

    {
        "id": "INC-2026-0894",
        "code": "OG-SPILL-0894",
        "name": "Singapore South Outer Anchorage Anomaly",
        "region": "Singapore Strait South",
        "latitude": 1.2150,
        "longitude": 103.7820,
        "status": "INVESTIGATION",
        "detected_at": "2026-09-01T22:40:00Z",
        "slick_area_km2": 8.75,
        "slick_perimeter_km": 18.2,
        "sar_confidence": 0.89,
        "lookalike_probability": 0.11,
        "estimated_age_hours": 12.0,

        # CHANGED:
        # The original S1B scene does not exist locally.
        # Connect this incident to the real local demo image.
        "scene_id": "kota_suria_pass",

        "primary_vessel_of_interest_id": "VESSEL-003",
    },

    {
        "id": "INC-2026-0881",
        "code": "OG-SPILL-0881",
        "name": "Riau Archipelago Offshore Slick",
        "region": "Riau Offshore Shipping Corridor",
        "latitude": 1.1040,
        "longitude": 104.1200,
        "status": "VALIDATED",
        "detected_at": "2026-08-31T06:10:00Z",
        "slick_area_km2": 22.10,
        "slick_perimeter_km": 41.5,
        "sar_confidence": 0.96,
        "lookalike_probability": 0.04,
        "estimated_age_hours": 8.0,

        # Real local SAR image
        "scene_id": "dht_edelweiss_pass",

        "primary_vessel_of_interest_id": "VESSEL-002",
    },
]


# ============================================================
# MOCK VESSELS
# ============================================================

MOCK_VESSELS = [
    {
        "id": "VESSEL-001",
        "mmsi": 636018432,
        "imo": 9482931,
        "name": "PACIFIC EXPLORER",
        "ship_type": "Crude Oil Tanker",
        "flag": "Liberia",
        "length_m": 274.0,
        "breadth_m": 48.0,
        "callsign": "A8XX9",
        "status": "UNDERWAY_USING_ENGINE",
    },

    {
        "id": "VESSEL-002",
        "mmsi": 352001928,
        "imo": 9612044,
        "name": "OCEAN GEMINI",
        "ship_type": "Chemical / Oil Products Tanker",
        "flag": "Panama",
        "length_m": 183.0,
        "breadth_m": 32.2,
        "callsign": "3FEW8",
        "status": "UNDERWAY_USING_ENGINE",
    },

    {
        "id": "VESSEL-003",
        "mmsi": 477291000,
        "imo": 9741029,
        "name": "EVER PRIDE",
        "ship_type": "Container Ship",
        "flag": "Hong Kong",
        "length_m": 334.0,
        "breadth_m": 45.8,
        "callsign": "VRQK5",
        "status": "UNDERWAY_USING_ENGINE",
    },

    {
        "id": "VESSEL-004",
        "mmsi": 235109400,
        "imo": 9304910,
        "name": "NORTH SEA VOYAGER",
        "ship_type": "Bulk Carrier",
        "flag": "United Kingdom",
        "length_m": 229.0,
        "breadth_m": 32.2,
        "callsign": "2GHT9",
        "status": "UNDERWAY_USING_ENGINE",
    },
]


# ============================================================
# MOCK SATELLITE SCENES
# ============================================================
# These are local demo scenes bundled with the project.
# Each incident points to a DIFFERENT SAR image so the real ML
# model produces different predictions for each incident.

MOCK_SATELLITE_SCENES = [
    {
        "id": "SCENE-001",
        "scene_id": "wakashio_reef",
        "platform": "Sentinel-1A",
        "mode": "IW",
        "polarization": "VV+VH",
        "acquisition_time": "2026-09-02T14:15:20Z",
        "pass_direction": "ASCENDING",
        "spatial_resolution_m": 10.0,
        # Demo geographic extent for the local sample.
        "bbox": [103.70, 1.15, 104.05, 1.40],
        "processing_status": "COMPLETED",
        "storage_uri": "local://wakashio_reef.jpg",
    },
    {
        "id": "SCENE-002",
        "scene_id": "kota_suria_pass",
        "platform": "Sentinel-1A",
        "mode": "IW",
        "polarization": "VV+VH",
        "acquisition_time": "2026-09-01T22:40:10Z",
        "pass_direction": "DESCENDING",
        "spatial_resolution_m": 10.0,
        "bbox": [103.60, 1.10, 103.95, 1.35],
        "processing_status": "COMPLETED",
        "storage_uri": "local://kota_suria_pass.jpg",
    },
    {
        "id": "SCENE-003",
        "scene_id": "dht_edelweiss_pass",
        "platform": "Sentinel-1A",
        "mode": "IW",
        "polarization": "VV+VH",
        "acquisition_time": "2026-08-31T06:10:00Z",
        "pass_direction": "DESCENDING",
        "spatial_resolution_m": 10.0,
        "bbox": [103.81, 1.22, 103.95, 1.34],
        "processing_status": "COMPLETED",
        "storage_uri": "local://dht_edelweiss_pass.jpg",
    },
]
