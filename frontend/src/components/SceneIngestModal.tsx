import React, { useState } from 'react';
import { X, Satellite, ArrowRight } from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const SceneIngestModal: React.FC = () => {
  const { isIngestModalOpen, setIngestModalOpen, ingestNewScene, isLoading } = useIncidentStore();
  const [sceneId, setSceneId] = useState('S1A_IW_GRDH_1SDV_20260902_MALACCA');

  if (!isIngestModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await ingestNewScene(sceneId);
    setIngestModalOpen(false);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(6, 17, 29, 0.85)',
      backdropFilter: 'blur(8px)',
      zIndex: 2000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div style={{
        width: '520px',
        backgroundColor: '#0a1725',
        border: '1px solid #1e3449',
        borderRadius: '12px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 50px rgba(0,0,0,0.8)',
        overflow: 'hidden'
      }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #1e3449', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0d1c2b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Satellite color="#32c7e8" size={20} />
            <h2 style={{ fontSize: '15px', fontWeight: 'bold', color: '#e7f0f7', margin: 0 }}>
              Ingest Sentinel-1 SAR Scene
            </h2>
          </div>
          <button onClick={() => setIngestModalOpen(false)} style={{ background: 'transparent', border: 'none', color: '#9fb2c3', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '20px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '11px', color: '#9fb2c3', marginBottom: '6px', fontWeight: 'bold' }}>
              SENTINEL-1 PRODUCT SCENE ID
            </label>
            <input
              type="text"
              value={sceneId}
              onChange={(e) => setSceneId(e.target.value)}
              className="mono-text"
              style={{
                width: '100%',
                padding: '10px',
                background: '#06111d',
                border: '1px solid #1e3449',
                borderRadius: '6px',
                color: '#e7f0f7',
                fontSize: '12px',
                outline: 'none'
              }}
              required
            />
          </div>

          <div style={{ background: '#0d1c2b', border: '1px solid #1e3449', borderRadius: '6px', padding: '12px', marginBottom: '20px', fontSize: '11px', color: '#9fb2c3' }}>
            <strong>Pipeline Actions Triggered:</strong>
            <ul style={{ margin: '6px 0 0 16px', padding: 0 }}>
              <li>Copernicus Data Space catalog discovery & download</li>
              <li>SAR VV/VH calibration, land masking & speckle filtering</li>
              <li>PyTorch U-Net pixel-level segmentation & geometry extraction</li>
              <li>Lagrangian retro-drift hindcasting & AIS spatio-temporal query</li>
            </ul>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" onClick={() => setIngestModalOpen(false)} className="btn-outline">
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="btn-primary">
              <span>{isLoading ? 'Processing Scene...' : 'Start Scene Ingestion'}</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
