from typing import Dict, Any

class ExplainableAttributionScorer:
    """
    OceanGuard Explainable Vessel Attribution Engine.
    Combines spatio-temporal correlation, drift trajectory alignment, vessel kinematics,
    and AIS behavioral anomalies to rank candidate vessels without declaring legal liability.
    
    Terminology rules strictly enforced:
    - Candidate Vessel
    - Vessel of Interest
    - Attribution Score
    - Correlation Evidence
    - Probable Origin Zone
    """
    
    DEFAULT_WEIGHTS = {
        "spatial": 0.25,
        "temporal": 0.20,
        "trajectory": 0.20,
        "speed": 0.10,
        "heading": 0.10,
        "ais_anomaly": 0.10,
        "vessel_context": 0.05,
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights if weights else self.DEFAULT_WEIGHTS

    def calculate_score(
        self,
        vessel: dict,
        distance_to_origin_km: float,
        time_delta_hours: float,
        trajectory_angle_diff_deg: float,
        speed_knots: float,
        heading_deg: float,
        slick_orientation_deg: float,
        anomaly_data: dict,
    ) -> dict:
        """
        Calculates normalized attribution correlation score (0 - 100) and returns component level explanation.
        """
        # 1. Spatial Score (25%) - Max score within 1km, decreasing to 0 at 25km
        spatial_raw = max(0.0, 1.0 - (distance_to_origin_km / 25.0))
        spatial_score = round(spatial_raw * 100.0, 1)

        # 2. Temporal Score (20%) - Max score within 0.5h of estimated origin time, 0 at >6h
        temporal_raw = max(0.0, 1.0 - (abs(time_delta_hours) / 6.0))
        temporal_score = round(temporal_raw * 100.0, 1)

        # 3. Trajectory Alignment (20%) - Vector dot product / angle difference
        traj_raw = max(0.0, 1.0 - (abs(trajectory_angle_diff_deg) / 90.0))
        trajectory_score = round(traj_raw * 100.0, 1)

        # 4. Speed Anomaly (10%) - Slow speed (3-8 knots) during transit increases score
        speed_anomaly = anomaly_data.get("has_speed_anomaly", False)
        if speed_anomaly or (3.0 <= speed_knots <= 7.0):
            speed_score = 92.0
        elif speed_knots < 3.0:
            speed_score = 75.0
        else:
            speed_score = 40.0

        # 5. Heading Alignment (10%) - Alignment with slick elongation major axis
        heading_diff = abs(heading_deg - slick_orientation_deg) % 180
        if heading_diff > 90:
            heading_diff = 180 - heading_diff
        heading_raw = max(0.0, 1.0 - (heading_diff / 90.0))
        heading_score = round(heading_raw * 100.0, 1)

        # 6. AIS Anomaly (10%) - Transmission gap or loitering
        ais_gap = anomaly_data.get("has_ais_gap", False)
        if ais_gap:
            ais_anomaly_score = 95.0
        elif anomaly_data.get("has_heading_anomaly", False):
            ais_anomaly_score = 80.0
        else:
            ais_anomaly_score = 25.0

        # 7. Vessel Context (5%) - Ship type risk weighting (Tanker / Cargo / Bulk / Other)
        ship_type = str(vessel.get("ship_type", "")).lower()
        if "tanker" in ship_type or "crude" in ship_type or "chemical" in ship_type:
            vessel_context_score = 95.0
        elif "cargo" in ship_type or "container" in ship_type:
            vessel_context_score = 70.0
        elif "tug" in ship_type or "supply" in ship_type:
            vessel_context_score = 60.0
        else:
            vessel_context_score = 40.0

        # Weighted Total Score (0 - 100)
        overall_score = (
            (spatial_score * self.weights["spatial"])
            + (temporal_score * self.weights["temporal"])
            + (trajectory_score * self.weights["trajectory"])
            + (speed_score * self.weights["speed"])
            + (heading_score * self.weights["heading"])
            + (ais_anomaly_score * self.weights["ais_anomaly"])
            + (vessel_context_score * self.weights["vessel_context"])
        )
        overall_score = round(overall_score, 1)

        # Assign Category & Confidence
        if overall_score >= 75.0:
            category = "Vessel of Interest"
            confidence_level = "CRITICAL"
        elif overall_score >= 50.0:
            category = "Candidate Vessel"
            confidence_level = "HIGH"
        elif overall_score >= 30.0:
            category = "Candidate Vessel"
            confidence_level = "MODERATE"
        else:
            category = "Candidate Vessel"
            confidence_level = "LOW"

        explanation = {
            "summary": f"Vessel '{vessel.get('name')}' exhibits a {overall_score}% spatio-temporal attribution correlation with the Probable Origin Zone.",
            "spatial_evidence": f"Passed within {round(distance_to_origin_km, 2)} km of origin centroid zone.",
            "temporal_evidence": f"Time window delta: {round(time_delta_hours, 2)} hours from retro-drift release estimate.",
            "trajectory_evidence": f"Course vector offset is {round(trajectory_angle_diff_deg, 1)}° relative to retro-drift line.",
            "kinematics_evidence": f"Transit speed: {round(speed_knots, 1)} kts, heading: {round(heading_deg, 1)}°.",
            "ais_evidence": f"AIS Transmission gap: {'Detected (' + str(anomaly_data.get('max_gap_minutes')) + ' min)' if ais_gap else 'Continuous'}.",
            "weights_used": self.weights
        }

        return {
            "vessel_id": vessel.get("id"),
            "vessel_name": vessel.get("name"),
            "mmsi": vessel.get("mmsi"),
            "overall_score": overall_score,
            "spatial_score": spatial_score,
            "temporal_score": temporal_score,
            "trajectory_score": trajectory_score,
            "speed_score": speed_score,
            "heading_score": heading_score,
            "ais_anomaly_score": ais_anomaly_score,
            "vessel_context_score": vessel_context_score,
            "category": category,
            "confidence_level": confidence_level,
            "explanation": explanation
        }
