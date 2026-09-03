from datetime import datetime
import json

class IncidentReportGenerator:
    """
    Generates structured, audit-compliant maritime oil spill incident investigation reports.
    Outputs HTML, JSON, and formatted Text reports with evidence provenance.
    """
    
    @staticmethod
    def generate_html_report(incident: dict, segmentation: dict, ocean_drift: dict, candidates: list) -> str:
        incident_id = incident.get("id", "INC-001")
        name = incident.get("name", "Unknown Spill Incident")
        detected_at = incident.get("detected_at", str(datetime.utcnow()))
        region = incident.get("region", "Unspecified Region")
        lat = incident.get("latitude", 0.0)
        lon = incident.get("longitude", 0.0)
        
        metrics = segmentation.get("metrics", {})
        env = ocean_drift.get("environmental_conditions", {})

        candidates_rows = ""
        for i, c in enumerate(candidates, 1):
            category_badge = f'<span style="background-color: {"#e43d3d" if c.get("overall_score", 0) >= 75 else "#1677e8"}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{c.get("category")}</span>'
            candidates_rows += f"""
            <tr style="border-bottom: 1px solid #1e3449;">
                <td style="padding: 10px; font-weight: bold;">#{i}</td>
                <td style="padding: 10px;">{c.get("vessel_name")} (MMSI: {c.get("mmsi")})</td>
                <td style="padding: 10px;">{category_badge}</td>
                <td style="padding: 10px; font-weight: bold; color: #32c7e8;">{c.get("overall_score")}%</td>
                <td style="padding: 10px; font-size: 12px; color: #9fb2c3;">{c.get("explanation", {}).get("spatial_evidence", "")}</td>
            </tr>
            """

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>OceanGuard Incident Report - {incident_id}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #06111d; color: #e7f0f7; margin: 0; padding: 40px; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #1677e8; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
        .title {{ font-size: 24px; color: #32c7e8; margin: 0; font-weight: bold; }}
        .badge {{ background: #1677e8; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .card-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #0a1725; border: 1px solid #1e3449; border-radius: 8px; padding: 20px; }}
        .card-title {{ font-size: 12px; color: #6f8496; text-transform: uppercase; margin-bottom: 8px; font-weight: bold; }}
        .card-value {{ font-size: 22px; color: #e7f0f7; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; background: #0a1725; border: 1px solid #1e3449; border-radius: 8px; overflow: hidden; margin-top: 20px; }}
        th {{ background: #0d1c2b; text-align: left; padding: 12px; color: #9fb2c3; font-size: 12px; text-transform: uppercase; border-bottom: 1px solid #1e3449; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #1e3449; font-size: 12px; color: #6f8496; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1 class="title">OceanGuard Maritime Incident Evidence Report</h1>
            <p style="color: #9fb2c3; margin: 4px 0 0 0;">Incident ID: {incident_id} | Region: {region}</p>
        </div>
        <span class="badge">OFFICIAL INVESTIGATION REPORT</span>
    </div>

    <div class="card-grid">
        <div class="card">
            <div class="card-title">Slick Extent Area</div>
            <div class="card-value" style="color: #e43d3d;">{metrics.get("area_km2", 0)} km²</div>
            <div style="font-size: 12px; color: #9fb2c3; margin-top: 4px;">Perimeter: {metrics.get("perimeter_km", 0)} km</div>
        </div>
        <div class="card">
            <div class="card-title">SAR Detection Confidence</div>
            <div class="card-value" style="color: #36c879;">{round(incident.get("sar_confidence", 0.95)*100, 1)}%</div>
            <div style="font-size: 12px; color: #9fb2c3; margin-top: 4px;">Look-alike score: {round(incident.get("lookalike_probability", 0.08)*100, 1)}%</div>
        </div>
        <div class="card">
            <div class="card-title">Environmental Wind / Current</div>
            <div class="card-value" style="color: #32c7e8;">{env.get("wind_speed_knots", 14.5)} kts</div>
            <div style="font-size: 12px; color: #9fb2c3; margin-top: 4px;">Current: {env.get("current_speed_knots", 1.8)} kts @ {env.get("current_direction_deg", 65)}°</div>
        </div>
    </div>

    <h2 style="font-size: 16px; color: #32c7e8; margin-top: 30px;">Top Candidate Vessels & Correlation Ranking</h2>
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Candidate Vessel</th>
                <th>Classification</th>
                <th>Attribution Score</th>
                <th>Spatio-Temporal Evidence</th>
            </tr>
        </thead>
        <tbody>
            {candidates_rows}
        </tbody>
    </table>

    <div class="card" style="margin-top: 30px;">
        <div class="card-title">Data Provenance & Audit Log</div>
        <p style="font-size: 13px; color: #9fb2c3; margin: 5px 0;">
            Sentinel-1 SAR Scene: <strong>{incident.get("scene_id", "S1A_IW_GRDH_1SDV_20260902")}</strong><br>
            Detection Algorithm: <strong>U-Net OilSpillSeg v1.4.2</strong> | Drift Engine: <strong>OceanParcels Lagrangian Retro-Drift</strong><br>
            Report Generated At: <strong>{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</strong>
        </p>
    </div>

    <div class="footer">
        OceanGuard Intelligence Platform &copy; 2026. This report presents spatio-temporal correlation evidence for investigative purposes only.
    </div>
</body>
</html>
"""
        return html_template
