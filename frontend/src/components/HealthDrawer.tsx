import React, { useEffect, useState } from 'react';
import { X, Activity, Server, Database, Radio, Cpu, HardDrive } from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const HealthDrawer: React.FC = () => {
  const { isHealthDrawerOpen, setHealthDrawerOpen } = useIncidentStore();
  const [telemetry, setTelemetry] = useState<any>(null);

  useEffect(() => {
    if (!isHealthDrawerOpen) return;
    fetch('/api/v1/system/health')
      .then(res => res.json())
      .then(data => setTelemetry(data))
      .catch(err => console.error(err));
  }, [isHealthDrawerOpen]);

  if (!isHealthDrawerOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, right: 0, bottom: 0,
      width: '360px',
      backgroundColor: '#0a1725',
      borderLeft: '1px solid #1e3449',
      zIndex: 2000,
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '-10px 0 30px rgba(0,0,0,0.6)',
      padding: '16px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid #1e3449', paddingBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} color="#36c879" />
          <h3 style={{ fontSize: '14px', fontWeight: 'bold', color: '#e7f0f7', margin: 0 }}>
            SYSTEM TELEMETRY & HEALTH
          </h3>
        </div>
        <button onClick={() => setHealthDrawerOpen(false)} style={{ background: 'transparent', border: 'none', color: '#9fb2c3', cursor: 'pointer' }}>
          <X size={18} />
        </button>
      </div>

      {telemetry ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ background: 'rgba(54, 200, 121, 0.1)', border: '1px solid #36c879', padding: '10px', borderRadius: '6px', color: '#36c879', fontSize: '12px', fontWeight: 'bold' }}>
            ● OVERALL SYSTEM STATUS: {telemetry.status}
          </div>

          <div style={{ fontSize: '11px', color: '#9fb2c3', marginTop: '6px' }}>
            SERVICE STATUS MONITOR:
          </div>

          {Object.entries(telemetry.services || {}).map(([key, val]) => (
            <div key={key} className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px' }}>
              <span style={{ fontSize: '11px', textTransform: 'capitalize', color: '#e7f0f7' }}>
                {key.replace(/_/g, ' ')}
              </span>
              <span style={{ fontSize: '10px', fontWeight: 'bold', color: '#36c879', background: 'rgba(54, 200, 121, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                {String(val)}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ color: '#9fb2c3', fontSize: '12px' }}>Loading system health telemetry...</div>
      )}
    </div>
  );
};
