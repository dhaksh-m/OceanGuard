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

  useEffect(() => {
    fetchInitialData();

    // Real-time live AIS vessel position stream ticker (2.5s interval)
    const interval = setInterval(() => {
      pollLiveVessels();
    }, 2500);

    return () => clearInterval(interval);
  }, [fetchInitialData, pollLiveVessels]);

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
