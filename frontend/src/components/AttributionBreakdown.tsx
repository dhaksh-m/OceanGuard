import React from 'react';
import { 
  Activity, 
  MapPin, 
  Clock, 
  Navigation, 
  Gauge, 
  Compass, 
  Radio, 
  ShieldCheck, 
  AlertCircle 
} from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const AttributionBreakdown: React.FC = () => {
  const { selectedAttribution } = useIncidentStore();

  if (!selectedAttribution) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#6f8496' }}>
        <AlertCircle size={32} color="#6f8496" style={{ margin: '0 auto 10px auto' }} />
        <p>Select a candidate vessel from the map or list to inspect attribution breakdown.</p>
      </div>
    );
  }

  const exp = selectedAttribution.explanation;
  const isVOI = selectedAttribution.category === 'Vessel of Interest';

  const factors = [
    { label: 'Spatial Correlation (25%)', score: selectedAttribution.spatial_score, desc: exp.spatial_evidence, icon: MapPin },
    { label: 'Temporal Correlation (20%)', score: selectedAttribution.temporal_score, desc: exp.temporal_evidence, icon: Clock },
    { label: 'Trajectory Alignment (20%)', score: selectedAttribution.trajectory_score, desc: exp.trajectory_evidence, icon: Navigation },
    { label: 'Speed Anomaly (10%)', score: selectedAttribution.speed_score, desc: exp.kinematics_evidence, icon: Gauge },
    { label: 'Heading Alignment (10%)', score: selectedAttribution.heading_score, desc: 'Heading vector aligned with slick major axis.', icon: Compass },
    { label: 'AIS Transmission (10%)', score: selectedAttribution.ais_anomaly_score, desc: exp.ais_evidence, icon: Radio },
    { label: 'Vessel Risk Context (5%)', score: selectedAttribution.vessel_context_score, desc: 'Tanker / Hazardous cargo vessel weighting.', icon: ShieldCheck },
  ];

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
      {/* Header Profile Card */}
      <div style={{
        background: '#0a1725',
        border: '1px solid',
        borderColor: isVOI ? '#ff3b30' : '#32c7e8',
        borderRadius: '8px',
        padding: '14px',
        marginBottom: '14px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <div>
            <span style={{ fontSize: '10px', textTransform: 'uppercase', color: '#6f8496', fontWeight: 'bold' }}>
              ATTRIBUTION INSPECTOR
            </span>
            <h3 style={{ fontSize: '16px', fontWeight: 'bold', color: '#e7f0f7', margin: '2px 0 0 0' }}>
              {selectedAttribution.vessel_name}
            </h3>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '22px', fontWeight: 'bold', color: isVOI ? '#ff3b30' : '#32c7e8' }}>
              {selectedAttribution.overall_score}%
            </div>
            <span style={{ fontSize: '10px', color: '#9fb2c3', textTransform: 'uppercase' }}>
              {selectedAttribution.category}
            </span>
          </div>
        </div>

        <p style={{ fontSize: '11px', color: '#9fb2c3', lineHeight: '1.4', background: '#06111d', padding: '8px', borderRadius: '4px', border: '1px solid #1e3449' }}>
          {exp.summary}
        </p>
      </div>

      {/* 7 Weighted Factor Components */}
      <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#9fb2c3', textTransform: 'uppercase', marginBottom: '10px' }}>
        CORRELATION FACTORS BREAKDOWN
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {factors.map((f, idx) => {
          const Icon = f.icon;
          return (
            <div key={idx} className="card-panel" style={{ padding: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Icon size={14} color="#32c7e8" />
                  <span style={{ fontSize: '12px', fontWeight: '600', color: '#e7f0f7' }}>{f.label}</span>
                </div>
                <span style={{ fontSize: '12px', fontWeight: 'bold', color: f.score >= 70 ? '#36c879' : f.score >= 40 ? '#f3b52f' : '#6f8496' }}>
                  {f.score}%
                </span>
              </div>

              <div style={{ width: '100%', height: '5px', background: '#06111d', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
                <div style={{
                  width: `${f.score}%`,
                  height: '100%',
                  background: f.score >= 70 ? '#36c879' : f.score >= 40 ? '#f3b52f' : '#6f8496'
                }} />
              </div>

              <div style={{ fontSize: '11px', color: '#9fb2c3' }}>
                {f.desc}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
