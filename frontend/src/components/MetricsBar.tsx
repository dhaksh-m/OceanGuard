import React from 'react';
import { TimelineSlider } from './TimelineSlider';
import { useIncidentStore } from '../store/useIncidentStore';

export const MetricsBar: React.FC = () => {
  const { activeIncident, segmentation, oceanDrift, attributionScores } = useIncidentStore();

  if (!activeIncident) return null;

  const topCandidate = attributionScores.length > 0 ? attributionScores[0] : null;

  return (
    <footer className="bottom-panel">
      <TimelineSlider />

      {/* Telemetry Metrics Badges */}
      <div style={{ display: 'flex', gap: '20px', marginLeft: '24px', borderLeft: '1px solid #1e3449', paddingLeft: '20px' }}>
        <div>
          <div style={{ fontSize: '10px', color: '#6f8496', textTransform: 'uppercase' }}>Slick Extent Area</div>
          <div style={{ fontSize: '15px', fontWeight: 'bold', color: '#e43d3d' }}>
            {activeIncident.slick_area_km2} km²
          </div>
        </div>

        <div>
          <div style={{ fontSize: '10px', color: '#6f8496', textTransform: 'uppercase' }}>Wind Vector</div>
          <div style={{ fontSize: '15px', fontWeight: 'bold', color: '#32c7e8' }}>
            {oceanDrift?.wind_speed_knots || 14.5} kts @ {oceanDrift?.wind_direction_deg || 225}°
          </div>
        </div>

        <div>
          <div style={{ fontSize: '10px', color: '#6f8496', textTransform: 'uppercase' }}>Top Candidate</div>
          <div style={{ fontSize: '15px', fontWeight: 'bold', color: '#ff3b30' }}>
            {topCandidate ? `${topCandidate.vessel_name} (${topCandidate.overall_score}%)` : 'None'}
          </div>
        </div>
      </div>
    </footer>
  );
};
