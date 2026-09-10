export type IncidentStatus = 
  | 'DETECTED' 
  | 'PROCESSING' 
  | 'VALIDATED' 
  | 'ORIGIN_ANALYSIS' 
  | 'VESSEL_CORRELATION' 
  | 'INVESTIGATION' 
  | 'RESOLVED' 
  | 'DISMISSED';

export interface Incident {
  id: string;
  code: string;
  name: string;
  region: string;
  latitude: number;
  longitude: number;
  status: IncidentStatus;
  detected_at: string;
  slick_area_km2: number;
  slick_perimeter_km: number;
  sar_confidence: number;
  lookalike_probability: number;
  estimated_age_hours: number;
  scene_id: string;
  primary_vessel_of_interest_id?: string;
}

export interface SpillGeometryMetrics {
  area_km2: number;
  perimeter_km: number;
  centroid_lat: number;
  centroid_lon: number;
  bbox: number[];
  major_axis_km: number;
  minor_axis_km: number;
  orientation_deg: number;
  compactness: number;
}

export interface SegmentationResult {
  incident_id: string;
  scene_id: string;
  mask_uri: string;
  confidence: number;
  lookalike_score: number;
  is_spill: boolean;
  metrics: SpillGeometryMetrics;
  polygon_geojson: any | null;
  water_ratio?: number;
  land_mask_provenance?: any;
}

export interface DriftParticle {
  particle_id: number;
  timestamp: string;
  lat: number;
  lon: number;
  probability: number;
}

export interface OceanDriftResult {
  incident_id: string;
  simulated_at: string;
  wind_speed_knots: number;
  wind_direction_deg: number;
  current_speed_knots: number;
  current_direction_deg: number;
  origin_zone_geojson: any;
  forecast_24h_geojson: any;
  forecast_48h_geojson: any;
  particles: DriftParticle[];
}

export interface Vessel {
  id: string;
  mmsi: number;
  imo?: number;
  name: string;
  ship_type: string;
  flag: string;
  length_m: number;
  breadth_m: number;
  callsign?: string;
  status: string;
}

export interface LiveVesselPosition {
  vessel_id: string;
  mmsi: number;
  imo?: number;
  name: string;
  ship_type: string;
  flag: string;
  latitude: number;
  longitude: number;
  speed_knots: number;
  course_deg: number;
  heading_deg: number;
  nav_status: string;
  signal_rssi_dbm: number;
  receiver_station: string;
  last_received: string;
  is_target_of_interest: boolean;
}

export interface AttributionScore {
  id: string;
  spill_id: string;
  vessel_id: string;
  vessel_name: string;
  mmsi: number;
  overall_score: number;
  spatial_score: number;
  temporal_score: number;
  trajectory_score: number;
  speed_score: number;
  heading_score: number;
  ais_anomaly_score: number;
  vessel_context_score: number;
  category: 'Candidate Vessel' | 'Vessel of Interest';
  confidence_level: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW';
  explanation: {
    summary: string;
    spatial_evidence: string;
    temporal_evidence: string;
    trajectory_evidence: string;
    kinematics_evidence: string;
    ais_evidence: string;
    weights_used: Record<string, number>;
  };
}

export interface EvidenceItem {
  id: string;
  incident_id: string;
  title: string;
  category: 'SAR_RASTER' | 'AIS_LOG' | 'DRIFT_SIMULATION' | 'WEATHER_DATA' | 'VESSEL_BEHAVIOR';
  description: string;
  created_at: string;
  file_url?: string;
  metadata_json: Record<string, any>;
}
