import React from 'react';
import { 
  FileCheck, 
  Download, 
  ExternalLink, 
  Database, 
  FileText, 
  Layers 
} from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const EvidenceLocker: React.FC = () => {
  const { activeIncident, evidenceItems } = useIncidentStore();

  if (!activeIncident) return null;

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '12px' }}>
      <div style={{ fontSize: '11px', fontWeight: 'bold', color: '#9fb2c3', textTransform: 'uppercase', marginBottom: '10px', display: 'flex', justifyContent: 'space-between' }}>
        <span>INCIDENT EVIDENCE LOCKER</span>
        <span style={{ color: '#32c7e8' }}>{evidenceItems.length} Artifacts</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {evidenceItems.map((item) => (
          <div key={item.id} className="card-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
              <span className="mono-text" style={{ fontSize: '10px', color: '#32c7e8', fontWeight: 'bold' }}>
                [{item.category}]
              </span>
              <span style={{ fontSize: '10px', color: '#6f8496' }}>
                {new Date(item.created_at).toLocaleTimeString()}
              </span>
            </div>

            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#e7f0f7', marginBottom: '4px' }}>
              {item.title}
            </div>

            <div style={{ fontSize: '11px', color: '#9fb2c3', marginBottom: '8px', lineHeight: '1.3' }}>
              {item.description}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #1e3449', paddingTop: '6px' }}>
              <span className="mono-text" style={{ fontSize: '10px', color: '#6f8496' }}>
                ID: {item.id}
              </span>
              <a
                href={item.file_url || '#'}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '11px',
                  color: '#1677e8',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Download size={12} />
                <span>Download</span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
