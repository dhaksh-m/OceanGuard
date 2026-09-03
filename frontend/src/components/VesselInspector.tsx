import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Ruler, 
  Activity, 
  ChevronRight, 
  Ship, 
  Layers, 
  FileCheck 
} from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';
import { AttributionBreakdown } from './AttributionBreakdown';
import { EvidenceLocker } from './EvidenceLocker';

export const VesselInspector: React.FC = () => {
  const { 
    activeIncident, 
    segmentation, 
    oceanDrift, 
    attributionScores, 
    selectedAttribution, 
    selectVessel,
    activeInspectorTab,
    setActiveInspectorTab,
    liveVessels 
  } = useIncidentStore();

  if (!activeIncident) return null;

  return (
    <aside className="inspector-right">
      {/* Inspector Tabs Bar */}
      <div style={{ display: 'flex', borderBottom: '1px solid #1e3449', background: '#0a1725' }}>
        {[
          { key: 'vessels', label: 'Candidates', icon: Ship },
          { key: 'attribution', label: 'Attribution', icon: Activity },
          { key: 'spill', label: 'Spill SAR', icon: Layers },
          { key: 'evidence', label: 'Evidence', icon: FileCheck },
        ].map((t) => {
          const Icon = t.icon;
          const isActive = activeInspectorTab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setActiveInspectorTab(t.key as any)}
              style={{
                flex: 1,
                padding: '10px 4px',
                background: isActive ? '#0d1c2b' : 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid #1677e8' : '2px solid transparent',
                color: isActive ? '#32c7e8' : '#6f8496',
                fontWeight: isActive ? 'bold' : 'normal',
                fontSize: '11px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '4px'
              }}
            >
              <Icon size={13} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Candidates Ranking List */}
      {activeInspectorTab === 'vessels' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#9fb2c3', textTransform: 'uppercase', marginBottom: '10px', display: 'flex', justifyContent: 'space-between' }}>
            <span>SPATIO-TEMPORAL CANDIDATES</span>
            <span style={{ color: '#32c7e8' }}>{attributionScores.length} Tracked</span>
          </div>

          <p style={{ fontSize: '11px', color: '#6f8496', marginBottom: '12px', background: '#0a1725', padding: '8px', borderRadius: '6px', border: '1px solid #1e3449' }}>
            ⓘ Ranked based on spatio-temporal correlation with the Probable Origin Zone. OceanGuard does not declare guilt; it provides investigative correlation evidence.
          </p>

          {attributionScores.map((candidate) => {
            const isSelected = selectedAttribution?.vessel_id === candidate.vessel_id;
            const isVOI = candidate.category === 'Vessel of Interest';

            return (
              <div
                key={candidate.vessel_id}
                onClick={() => selectVessel(candidate)}
                style={{
                  background: isSelected ? '#12263a' : '#0a1725',
                  border: '1px solid',
                  borderColor: isSelected ? '#ff3b30' : isVOI ? '#ff9f1c' : '#1e3449',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '10px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 'bold', color: '#e7f0f7', fontSize: '13px' }}>
                    {candidate.vessel_name}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 'bold',
                    padding: '2px 8px',
                    borderRadius: '10px',
                    background: isVOI ? 'rgba(240, 68, 68, 0.2)' : 'rgba(50, 199, 232, 0.2)',
                    color: isVOI ? '#ff3b30' : '#32c7e8'
                  }}>
                    {candidate.overall_score}%
                  </span>
                </div>

                <div style={{ fontSize: '11px', color: '#9fb2c3', marginBottom: '8px' }}>
                  MMSI: <span className="mono-text">{candidate.mmsi}</span> | Classification: <strong style={{ color: isVOI ? '#ff3b30' : '#32c7e8' }}>{candidate.category}</strong>
                </div>

                {/* Score Progress Bar */}
                <div style={{ width: '100%', height: '6px', background: '#06111d', borderRadius: '3px', overflow: 'hidden', marginBottom: '8px' }}>
                  <div style={{
                    width: `${candidate.overall_score}%`,
                    height: '100%',
                    background: isVOI ? 'linear-gradient(90deg, #ff9f1c, #ff3b30)' : 'linear-gradient(90deg, #1677e8, #32c7e8)'
                  }} />
                </div>

                <div style={{ fontSize: '11px', color: '#6f8496', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>{candidate.explanation.spatial_evidence}</span>
                  <ChevronRight size={14} color="#32c7e8" />
                </div>
              </div>
            );
          })}

          {/* Real-Time Live AIS Feed Section */}
          <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#36c879', textTransform: 'uppercase', margin: '16px 0 8px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className="pulse-dot" style={{ width: '6px', height: '6px', background: '#36c879', borderRadius: '50%', display: 'inline-block' }} />
            <span>REAL-TIME AIS STREAMING TICKER</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {liveVessels.map((lv) => (
              <div key={lv.mmsi} style={{ background: '#0a1725', border: '1px solid #1e3449', borderRadius: '6px', padding: '8px 10px', fontSize: '11px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                  <strong style={{ color: lv.is_target_of_interest ? '#ff3b30' : '#32c7e8' }}>{lv.name}</strong>
                  <span className="mono-text" style={{ color: '#36c879' }}>{lv.speed_knots} kts</span>
                </div>
                <div style={{ color: '#9fb2c3', fontSize: '10px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Pos: <strong className="mono-text" style={{ color: '#e7f0f7' }}>{lv.latitude}, {lv.longitude}</strong></span>
                  <span>Hdg: <strong style={{ color: '#e7f0f7' }}>{lv.heading_deg}°</strong></span>
                </div>
                <div style={{ color: '#6f8496', fontSize: '9px', marginTop: '2px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Receiver: {lv.receiver_station}</span>
                  <span>RSSI: {lv.signal_rssi_dbm} dBm</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Deep-Dive Attribution Breakdown */}
      {activeInspectorTab === 'attribution' && (
        <AttributionBreakdown />
      )}

      {/* Tab 3: Spill SAR Metrics */}
      {activeInspectorTab === 'spill' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
          <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#9fb2c3', textTransform: 'uppercase', marginBottom: '10px' }}>
            SENTINEL-1 SAR SEGMENTATION METRICS
          </div>

          {segmentation && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="card-panel">
                <div style={{ fontSize: '11px', color: '#6f8496' }}>Slick Surface Area</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#e43d3d' }}>
                  {segmentation.metrics.area_km2} km²
                </div>
                <div style={{ fontSize: '11px', color: '#9fb2c3' }}>Perimeter: {segmentation.metrics.perimeter_km} km</div>
              </div>

              <div className="card-panel" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <div style={{ fontSize: '10px', color: '#6f8496' }}>SAR Confidence</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#36c879' }}>
                    {Math.round(segmentation.confidence * 100)}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '10px', color: '#6f8496' }}>Look-alike Risk</div>
                  <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#f3b52f' }}>
                    {Math.round(segmentation.lookalike_score * 100)}%
                  </div>
                </div>
              </div>

              <div className="card-panel">
                <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#e7f0f7', marginBottom: '6px' }}>Geometry & Orientation</div>
                <div style={{ fontSize: '11px', color: '#9fb2c3', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div>Major Axis Length: <strong>{segmentation.metrics.major_axis_km} km</strong></div>
                  <div>Minor Axis Length: <strong>{segmentation.metrics.minor_axis_km} km</strong></div>
                  <div>Orientation Angle: <strong>{segmentation.metrics.orientation_deg}°</strong></div>
                  <div>Compactness Index: <strong>{segmentation.metrics.compactness}</strong></div>
                  <div>Centroid: <span className="mono-text">{segmentation.metrics.centroid_lat}, {segmentation.metrics.centroid_lon}</span></div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Evidence Locker */}
      {activeInspectorTab === 'evidence' && (
        <EvidenceLocker />
      )}
    </aside>
  );
};
