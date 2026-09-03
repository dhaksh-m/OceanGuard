import React from 'react';
import { X, Download, FileText, Printer } from 'lucide-react';
import { useIncidentStore } from '../store/useIncidentStore';

export const IncidentReportModal: React.FC = () => {
  const { isReportModalOpen, setReportModalOpen, activeIncident } = useIncidentStore();

  if (!isReportModalOpen || !activeIncident) return null;

  const htmlUrl = `/api/v1/reports/${activeIncident.id}/html`;
  const jsonUrl = `/api/v1/reports/${activeIncident.id}/json`;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(6, 17, 29, 0.85)',
      backdropFilter: 'blur(8px)',
      zIndex: 2000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div style={{
        width: '900px',
        maxHeight: '90vh',
        backgroundColor: '#0a1725',
        border: '1px solid #1e3449',
        borderRadius: '12px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 50px rgba(0,0,0,0.8)',
        overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #1e3449', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0d1c2b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText color="#32c7e8" size={20} />
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', color: '#e7f0f7', margin: 0 }}>
              Official Incident Investigation Evidence Report [{activeIncident.code}]
            </h2>
          </div>
          <button
            onClick={() => setReportModalOpen(false)}
            style={{ background: 'transparent', border: 'none', color: '#9fb2c3', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Report Preview Frame */}
        <div style={{ flex: 1, minHeight: '500px', background: '#06111d' }}>
          <iframe
            src={htmlUrl}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="Incident Report Preview"
          />
        </div>

        {/* Modal Footer Controls */}
        <div style={{ padding: '14px 20px', borderTop: '1px solid #1e3449', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0d1c2b' }}>
          <span style={{ fontSize: '11px', color: '#6f8496' }}>
            Audit compliance version: <strong>OceanGuard Report v1.0.0</strong>
          </span>

          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href={jsonUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-outline"
              style={{ textDecoration: 'none', fontSize: '12px' }}
            >
              <Download size={14} />
              <span>Export JSON</span>
            </a>

            <a
              href={htmlUrl}
              target="_blank"
              rel="noreferrer"
              className="btn-primary"
              style={{ textDecoration: 'none', fontSize: '12px' }}
            >
              <Printer size={14} />
              <span>Print / Save PDF</span>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
