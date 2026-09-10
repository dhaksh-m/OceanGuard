import React from 'react';
import { 
  ShieldAlert, 
  Layers, 
  FileText, 
  PlusCircle, 
  Activity, 
  Anchor,
  Eye,
  Crosshair,
  Satellite
} from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const Header: React.FC = () => {
  const { 
    incidents, 
    activeIncident, 
    selectIncident, 
    setReportModalOpen, 
    setIngestModalOpen, 
    setHealthDrawerOpen,
    isLoading,
    sensorMode,
    isCockpitMode,
    followedMmsi,
    wsConnected,
    liveVessels,
    segmentation
  } = useIncidentStore();

  return (
    <header className="header-bar">
      {/* Brand & Live Telemetry Badge */}
      <div className="flex items-center gap-4" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ 
            background: 'linear-gradient(135deg, #1677e8, #32c7e8)', 
            padding: '6px', 
            borderRadius: '8px', 
            display: 'flex' 
          }}>
            <ShieldAlert size={20} color="#ffffff" />
          </div>
          <div>
            <h1 style={{ fontSize: '16px', fontWeight: 'bold', color: '#e7f0f7', margin: 0, letterSpacing: '0.5px' }}>
              OCEANGUARD
            </h1>
            <span style={{ fontSize: '10px', color: '#6f8496', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
              Maritime Intelligence Console
            </span>
          </div>
        </div>

        <div className="badge-live" title={wsConnected ? 'WebSocket LIVE' : 'Polling'}>
          <span className="pulse-dot" />
          <span>● {wsConnected ? 'LIVE • WS' : 'LIVE'} • {liveVessels.length} CONTACTS</span>
        </div>
        {/* God's Eye mode badge */}
        <div style={{ background: sensorMode !== 'normal' ? 'rgba(22,119,232,0.18)' : 'rgba(50,199,232,0.12)', border: `1px solid ${sensorMode!=='normal'? '#1677e8' : '#1e3449'}`, color: sensorMode!=='normal' ? '#32c7e8' : '#9fb2c3', padding: '3px 8px', borderRadius: '999px', fontSize: '10px', fontWeight: 700, letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '5px' }}>
          <Satellite size={12} />
          <span>GOD'S EYE {sensorMode.toUpperCase()}</span>
        </div>
        {isCockpitMode && (
          <div style={{ background: 'rgba(255,59,48,0.18)', border: '1px solid #ff3b30', color: '#ff9f1c', padding: '3px 8px', borderRadius: '999px', fontSize: '10px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Crosshair size={12} />
            <span>COCKPIT MMSI {followedMmsi}</span>
          </div>
        )}
      </div>

      {/* Incident Switcher & Action Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Incident Select Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#0d1c2b', border: '1px solid #1e3449', padding: '4px 10px', borderRadius: '6px' }}>
          <Anchor size={14} color="#32c7e8" />
          <span style={{ fontSize: '11px', color: '#6f8496' }}>Incident:</span>
          <select 
            value={activeIncident?.id || ''} 
            onChange={(e) => {
              const found = incidents.find(i => i.id === e.target.value);
              if (found) selectIncident(found);
            }}
            disabled={isLoading}
            style={{ 
              background: 'transparent', 
              color: '#e7f0f7', 
              border: 'none', 
              fontSize: '12px', 
              fontWeight: '600', 
              outline: 'none',
              cursor: 'pointer' 
            }}
          >
            {incidents.map(inc => (
              <option key={inc.id} value={inc.id} style={{ background: '#0a1725', color: '#e7f0f7' }}>
                [{inc.code}] {inc.name}
              </option>
            ))}
          </select>
        </div>

        {/* Ingest Scene Button */}
        <button 
          className="btn-outline" 
          onClick={() => setIngestModalOpen(true)}
          style={{ fontSize: '12px' }}
        >
          <PlusCircle size={14} color="#32c7e8" />
          <span>Ingest SAR Scene</span>
        </button>

        {/* Generate Evidence Report Button */}
        <button 
          className="btn-primary" 
          onClick={() => setReportModalOpen(true)}
          style={{ fontSize: '12px' }}
        >
          <FileText size={14} />
          <span>Evidence Report</span>
        </button>

        {/* System Health Drawer Button */}
        <button 
          onClick={() => setHealthDrawerOpen(true)}
          style={{ 
            background: 'transparent', 
            border: '1px solid #1e3449', 
            borderRadius: '6px', 
            padding: '6px 8px', 
            color: '#36c879', 
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center'
          }}
          title="System Health & Telemetry"
        >
          <Activity size={16} />
        </button>
      </div>
    </header>
  );
};
