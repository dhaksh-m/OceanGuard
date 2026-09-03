import numpy as np

class AISAnomalyDetector:
    """
    Analyzes vessel trajectory & behavior logs to detect potential operational anomalies:
    1. Speed Drop / Tank Washing / Discharge Speed Anomaly (e.g. slowing down from 14 knots to 4 knots in open water)
    2. Heading Deviation / Loitering
    3. AIS Transmission Gaps (Dark Vessel signal dropouts)
    """
    @staticmethod
    def analyze_trajectory(positions: list, origin_zone: dict = None) -> dict:
        if not positions or len(positions) < 2:
            return {
                "has_speed_anomaly": False,
                "has_heading_anomaly": False,
                "has_ais_gap": False,
                "anomaly_score": 0.0,
                "details": "Insufficient trajectory positions"
            }

        speeds = [p.get("speed_knots", 0.0) for p in positions]
        headings = [p.get("heading_deg", 0.0) for p in positions]

        # 1. Speed Anomaly Check
        max_speed = max(speeds) if speeds else 0
        min_speed = min(speeds) if speeds else 0
        speed_delta = max_speed - min_speed
        has_speed_anomaly = (max_speed > 10.0 and min_speed < 5.0) or (speed_delta > 7.0)

        # 2. Heading Anomaly Check
        heading_diffs = [abs(headings[i] - headings[i-1]) for i in range(1, len(headings))]
        max_heading_change = max(heading_diffs) if heading_diffs else 0
        has_heading_anomaly = max_heading_change > 45.0

        # 3. AIS Gap Check (e.g., > 45 mins between consecutive AIS reports)
        has_ais_gap = False
        max_gap_minutes = 0.0
        for i in range(1, len(positions)):
            t1 = positions[i-1].get("timestamp")
            t2 = positions[i].get("timestamp")
            if t1 and t2:
                try:
                    dt = abs((t2 - t1).total_seconds()) / 60.0
                    if dt > max_gap_minutes:
                        max_gap_minutes = dt
                except Exception:
                    pass

        has_ais_gap = max_gap_minutes > 45.0

        # Anomaly composite calculation
        anomaly_score = 0.0
        if has_speed_anomaly: anomaly_score += 0.40
        if has_heading_anomaly: anomaly_score += 0.30
        if has_ais_gap: anomaly_score += 0.30

        return {
            "has_speed_anomaly": has_speed_anomaly,
            "has_heading_anomaly": has_heading_anomaly,
            "has_ais_gap": has_ais_gap,
            "max_gap_minutes": round(max_gap_minutes, 1),
            "max_heading_change_deg": round(max_heading_change, 1),
            "speed_min_knots": min_speed,
            "speed_max_knots": max_speed,
            "anomaly_score": round(min(1.0, anomaly_score), 2)
        }
