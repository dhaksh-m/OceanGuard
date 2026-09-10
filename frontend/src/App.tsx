import React, { useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { MapView } from './components/MapView';
import { VesselInspector } from './components/VesselInspector';
import { MetricsBar } from './components/MetricsBar';
import { IncidentReportModal } from './components/IncidentReportModal';
import { SceneIngestModal } from './components/SceneIngestModal';
import { HealthDrawer } from './components/HealthDrawer';
import { useIncidentStore } from './store/useIncidentStore';

export const App: React.FC = () => {
  const { fetchInitialData, pollLiveVessels } = useIncidentStore();
  const setWsConnected = useIncidentStore(state => state.setWsConnected);

  useEffect(() => {
    fetchInitialData();

    // Real-time live AIS vessel position stream ticker (2.5s interval) - fallback polling
    const interval = setInterval(() => {
      pollLiveVessels();
    }, 2500);

    // God's Eye WebSocket telemetry (ws://localhost:8000/ws/telemetry) - try WS, fallback to polling
    let ws: WebSocket | null = null;
    let wsTries = 0;
    const connectWs = () => {
      const wsUrl = (import.meta as any).env?.VITE_WS_BASE_URL || `ws://${window.location.hostname}:8000/ws/telemetry`;
      try {
        ws = new WebSocket(wsUrl);
        ws.onopen = () => {
          setWsConnected(true);
          wsTries = 0;
        };
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data);
            if (data.type === 'VESSEL_TELEMETRY_UPDATE' && data.vessels) {
              // Patch store directly for low latency
              useIncidentStore.setState({ liveVessels: data.vessels.map((v: any) => ({
                vessel_id: `VESSEL-${v.mmsi}`,
                mmsi: v.mmsi,
                imo: v.imo || 0,
                name: v.name,
                ship_type: v.ship_type || 'Unknown',
                flag: v.flag || 'Unknown',
                latitude: v.lat ?? v.latitude,
                longitude: v.lon ?? v.longitude,
                speed_knots: v.speed_knots,
                heading_deg: v.heading_deg,
                course_deg: v.course_deg || v.heading_deg,
                trail: v.trail || [],
                is_target_of_interest: v.is_target_of_interest ?? false,
                threat_score: v.threat_score,
                receiver_station: v.receiver_station || 'WS-STREAM',
                signal_rssi_dbm: v.signal_rssi_dbm || -60,
                draft_m: v.draft_m,
                destination: v.destination,
              })) });
            }
          } catch {}
        };
        ws.onclose = () => {
          setWsConnected(false);
          if (wsTries < 5) {
            wsTries++;
            setTimeout(connectWs, 3000 * wsTries);
          }
        };
        ws.onerror = () => {
          try { ws?.close(); } catch {}
        };
      } catch {
        setWsConnected(false);
      }
    };
    // Delay WS connect slightly to let initial poll happen
    const wsTimer = setTimeout(connectWs, 1200);

    return () => {
      clearInterval(interval);
      clearTimeout(wsTimer);
      try { ws?.close(); } catch {}
      setWsConnected(false);
    };
  }, [fetchInitialData, pollLiveVessels, setWsConnected]);

  return (
    <div className="app-container">
      <Header />

      <main className="main-content">
        <Sidebar />
        <MapView />
        <VesselInspector />
      </main>

      <MetricsBar />

      {/* Modals & Drawers */}
      <IncidentReportModal />
      <SceneIngestModal />
      <HealthDrawer />
    </div>
  );
};

export default App;
