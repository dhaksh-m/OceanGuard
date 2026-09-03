-- OceanGuard PostGIS Database Initialization Schema
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Vessels Table
CREATE TABLE IF NOT EXISTS vessels (
    id VARCHAR(64) PRIMARY KEY,
    mmsi BIGINT UNIQUE NOT NULL,
    imo BIGINT,
    name VARCHAR(255) NOT NULL,
    ship_type VARCHAR(100) NOT NULL,
    flag VARCHAR(100),
    length_m NUMERIC(6, 2),
    breadth_m NUMERIC(6, 2),
    callsign VARCHAR(32),
    status VARCHAR(64),
    metadata_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. AIS Positions Time-Series Table
CREATE TABLE IF NOT EXISTS ais_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vessel_id VARCHAR(64) REFERENCES vessels(id) ON DELETE CASCADE,
    mmsi BIGINT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    speed_knots NUMERIC(5, 2),
    course_deg NUMERIC(5, 2),
    heading_deg NUMERIC(5, 2),
    nav_status VARCHAR(64),
    geom GEOMETRY(Point, 4326),
    source VARCHAR(64) DEFAULT 'NMEA_STREAM'
);
CREATE INDEX IF NOT EXISTS idx_ais_spatial ON ais_positions USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_ais_time_mmsi ON ais_positions (mmsi, timestamp DESC);

-- 3. Satellite Scenes Table
CREATE TABLE IF NOT EXISTS satellite_scenes (
    id VARCHAR(64) PRIMARY KEY,
    scene_id VARCHAR(128) UNIQUE NOT NULL,
    platform VARCHAR(64) NOT NULL,
    mode VARCHAR(32),
    polarization VARCHAR(32),
    acquisition_time TIMESTAMP WITH TIME ZONE NOT NULL,
    pass_direction VARCHAR(32),
    spatial_resolution_m NUMERIC(6, 2),
    bbox NUMERIC[],
    storage_uri VARCHAR(512),
    processing_status VARCHAR(32) DEFAULT 'COMPLETED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Spill Events Table
CREATE TABLE IF NOT EXISTS spill_events (
    id VARCHAR(64) PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(255),
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'DETECTED',
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    slick_area_km2 NUMERIC(8, 2),
    slick_perimeter_km NUMERIC(8, 2),
    sar_confidence NUMERIC(4, 3),
    lookalike_probability NUMERIC(4, 3),
    estimated_age_hours NUMERIC(5, 2),
    scene_id VARCHAR(64) REFERENCES satellite_scenes(id),
    primary_vessel_id VARCHAR(64) REFERENCES vessels(id),
    geom GEOMETRY(Polygon, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_spill_spatial ON spill_events USING GIST (geom);

-- 5. Spill Drift Particles Table
CREATE TABLE IF NOT EXISTS spill_particles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    spill_id VARCHAR(64) REFERENCES spill_events(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL,
    longitude NUMERIC(9, 6) NOT NULL,
    probability NUMERIC(4, 3),
    simulation_run VARCHAR(64)
);

-- 6. Attribution Results Table
CREATE TABLE IF NOT EXISTS attribution_results (
    id VARCHAR(64) PRIMARY KEY,
    spill_id VARCHAR(64) REFERENCES spill_events(id) ON DELETE CASCADE,
    vessel_id VARCHAR(64) REFERENCES vessels(id) ON DELETE CASCADE,
    overall_score NUMERIC(5, 2) NOT NULL,
    spatial_score NUMERIC(5, 2),
    temporal_score NUMERIC(5, 2),
    trajectory_score NUMERIC(5, 2),
    speed_score NUMERIC(5, 2),
    heading_score NUMERIC(5, 2),
    ais_anomaly_score NUMERIC(5, 2),
    vessel_context_score NUMERIC(5, 2),
    category VARCHAR(64) NOT NULL,
    explanation_json JSONB,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
