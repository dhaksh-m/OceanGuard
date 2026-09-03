import React, { useState } from 'react';
import { 
  Radio, 
  Layers, 
  Eye, 
  EyeOff, 
  Search, 
  Filter, 
  Compass, 
  Wind, 
  Waves, 
  Target 
} from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const Sidebar: React.FC = () => {
  const { 
    incidents, 
    activeIncident, 
    selectIncident, 
    layers, 
    toggleLayer,
    isLoading 
  } = useIncidentStore();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filteredIncidents = incidents.filter(inc => {
    const matchesSearch = inc.name.toLowerCase().includes(search.toLowerCase()) || 
                          inc.code.toLowerCase().includes(search.toLowerCase()) ||
                          inc.region.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || inc.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <aside className="sidebar-left">
      {/* Incidents List Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #1e3449', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={16} color="#1677e8" />
          <span style={{ fontWeight: 'bold', fontSize: '13px', color: '#e7f0f7' }}>ACTIVE INCIDENTS</span>
        </div>
        <span style={{ background: '#0a1725', color: '#32c7e8', padding: '2px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: 'bold' }}>
          {incidents.length} Active
        </span>
      </div>

      {/* Search & Filter Bar */}
      <div style={{ padding: '10px 12px', borderBottom: '1px solid #1e3449' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0a1725', border: '1px solid #1e3449', borderRadius: '6px', padding: '6px 10px', marginBottom: '8px' }}>
          <Search size={14} color="#6f8496" />
          <input 
            type="text"
            placeholder="Search incident, region, code..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ background: 'transparent', border: 'none', color: '#e7f0f7', outline: 'none', fontSize: '12px', width: '100%' }}
          />
        </div>

        <div style={{ display: 'flex', gap: '4px' }}>
          {['ALL', 'VESSEL_CORRELATION', 'INVESTIGATION', 'VALIDATED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              style={{
                fontSize: '10px',
                padding: '3px 8px',
                borderRadius: '4px',
                border: '1px solid',
                borderColor: statusFilter === st ? '#1677e8' : '#1e3449',
                background: statusFilter === st ? 'rgba(22, 119, 232, 0.2)' : 'transparent',
                color: statusFilter === st ? '#32c7e8' : '#6f8496',
                cursor: 'pointer',
                fontWeight: statusFilter === st ? 'bold' : 'normal'
              }}
            >
              {st === 'ALL' ? 'All' : st.split('_')[0]}
            </button>
          ))}
        </div>
      </div>

      {/* Incidents Feed */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
        {filteredIncidents.map((inc) => {
          const isActive = activeIncident?.id === inc.id;
          return (
            <div
              key={inc.id}
              onClick={() => selectIncident(inc)}
              style={{
                background: isActive ? '#12263a' : '#0a1725',
                border: '1px solid',
                borderColor: isActive ? '#1677e8' : '#1e3449',
                borderRadius: '8px',
                padding: '10px',
                marginBottom: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
                <span className="mono-text" style={{ fontSize: '11px', color: '#32c7e8', fontWeight: 'bold' }}>
                  {inc.code}
                </span>
                <span style={{ 
                  fontSize: '10px', 
                  padding: '2px 6px', 
                  borderRadius: '4px', 
                  background: inc.status === 'INVESTIGATION' ? 'rgba(240, 68, 68, 0.2)' : 'rgba(22, 119, 232, 0.2)',
                  color: inc.status === 'INVESTIGATION' ? '#f04444' : '#1677e8',
                  fontWeight: '600'
                }}>
                  {inc.status}
                </span>
              </div>

              <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#e7f0f7', marginBottom: '4px' }}>
                {inc.name}
              </div>

              <div style={{ fontSize: '11px', color: '#9fb2c3', marginBottom: '6px' }}>
                {inc.region}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#6f8496', borderTop: '1px solid #1e3449', paddingTop: '6px' }}>
                <span>Area: <strong style={{ color: '#e43d3d' }}>{inc.slick_area_km2} km²</strong></span>
                <span>Confidence: <strong style={{ color: '#36c879' }}>{Math.round(inc.sar_confidence * 100)}%</strong></span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Map Layer Controls Panel */}
      <div style={{ padding: '12px', borderTop: '1px solid #1e3449', background: '#0a1725' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', fontSize: '11px', fontWeight: 'bold', color: '#9fb2c3' }}>
          <Layers size={14} color="#32c7e8" />
          <span>GIS MAP LAYERS</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
          {[
            { key: 'spillPolygon', label: 'Spill Slick', icon: Target, color: '#e43d3d' },
            { key: 'probableOriginZone', label: 'Origin Zone', icon: Compass, color: '#32c7e8' },
            { key: 'forecast24h', label: '24h Forecast', icon: Radio, color: '#ff9f1c' },
            { key: 'forecast48h', label: '48h Forecast', icon: Radio, color: '#ffd23f' },
            { key: 'vessels', label: 'AIS Vessels', icon: Compass, color: '#38d4e8' },
            { key: 'vesselTrails', label: 'Vessel Trails', icon: Compass, color: '#27d17f' },
            { key: 'windVectors', label: 'Wind Field', icon: Wind, color: '#9fb2c3' },
            { key: 'currentVectors', label: 'Ocean Current', icon: Waves, color: '#1677e8' },
          ].map((l) => {
            const isVisible = layers[l.key as keyof typeof layers];
            return (
              <button
                key={l.key}
                onClick={() => toggleLayer(l.key as keyof typeof layers)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '5px 8px',
                  borderRadius: '4px',
                  background: isVisible ? '#0d1c2b' : 'transparent',
                  border: '1px solid',
                  borderColor: isVisible ? '#1e3449' : 'transparent',
                  color: isVisible ? '#e7f0f7' : '#6f8496',
                  cursor: 'pointer',
                  fontSize: '10px',
                  textAlign: 'left'
                }}
              >
                {isVisible ? <Eye size={12} color={l.color} /> : <EyeOff size={12} color="#6f8496" />}
                <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {l.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
