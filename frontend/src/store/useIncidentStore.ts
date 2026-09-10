import { create } from 'zustand';
import { 
  Incident, 
  SegmentationResult, 
  OceanDriftResult, 
  Vessel, 
  AttributionScore, 
  EvidenceItem 
} from '../types';
import * as api from '../services/api';

interface IncidentState {
  incidents: Incident[];
  activeIncident: Incident | null;
  segmentation: SegmentationResult | null;
  oceanDrift: OceanDriftResult | null;
  vessels: Vessel[];
  liveVessels: any[];
  attributionScores: AttributionScore[];
  selectedAttribution: AttributionScore | null;
  evidenceItems: EvidenceItem[];
  
  // Layer Visibility Controls
  layers: {
    spillPolygon: boolean;
    probableOriginZone: boolean;
    forecast24h: boolean;
    forecast48h: boolean;
    vessels: boolean;
    vesselTrails: boolean;
    windVectors: boolean;
    currentVectors: boolean;
    sarOverlay: boolean;
  };

  // Timeline Controls
  timeline: {
    currentTimeHoursAgo: number; // 0.0 to 12.0 hours ago
    isPlaying: boolean;
    playbackSpeed: number; // 1x, 2x, 5x
  };

  // UI Panels
  activeInspectorTab: 'spill' | 'vessels' | 'attribution' | 'evidence';
  isReportModalOpen: boolean;
  isIngestModalOpen: boolean;
  isHealthDrawerOpen: boolean;
  isLoading: boolean;

  // God's Eye View state
  sensorMode: 'normal' | 'crt' | 'nvg' | 'thermal' | 'flir' | 'noir' | 'snow';
  isHudEnabled: boolean;
  isDetectionOverlay: boolean;
  isCockpitMode: boolean;
  followedMmsi: number | null;
  mapBase: 'dark' | 'satellite' | 'ocean';
  wsConnected: boolean;

  // Actions
  fetchInitialData: () => Promise<void>;
  pollLiveVessels: () => Promise<void>;
  selectIncident: (incident: Incident) => Promise<void>;
  selectVessel: (attribution: AttributionScore | null) => void;
  toggleLayer: (layerName: keyof IncidentState['layers']) => void;
  setTimelineTime: (hoursAgo: number) => void;
  togglePlayback: () => void;
  setPlaybackSpeed: (speed: number) => void;
  setActiveInspectorTab: (tab: IncidentState['activeInspectorTab']) => void;
  setReportModalOpen: (open: boolean) => void;
  setIngestModalOpen: (open: boolean) => void;
  setHealthDrawerOpen: (open: boolean) => void;
  ingestNewScene: (sceneId: string) => Promise<void>;
  setSensorMode: (mode: IncidentState['sensorMode']) => void;
  setHudEnabled: (v: boolean) => void;
  setDetectionOverlay: (v: boolean) => void;
  setCockpitMode: (v: boolean, mmsi?: number | null) => void;
  setMapBase: (base: IncidentState['mapBase']) => void;
  setWsConnected: (v: boolean) => void;
}

export const useIncidentStore = create<IncidentState>((set, get) => ({
  incidents: [],
  activeIncident: null,
  segmentation: null,
  oceanDrift: null,
  vessels: [],
  liveVessels: [],
  attributionScores: [],
  selectedAttribution: null,
  evidenceItems: [],

  layers: {
    spillPolygon: true,
    probableOriginZone: true,
    forecast24h: true,
    forecast48h: true,
    vessels: true,
    vesselTrails: true,
    windVectors: true,
    currentVectors: true,
    sarOverlay: true,
  },

  timeline: {
    currentTimeHoursAgo: 0.0,
    isPlaying: false,
    playbackSpeed: 1,
  },

  activeInspectorTab: 'vessels',
  isReportModalOpen: false,
  isIngestModalOpen: false,
  isHealthDrawerOpen: false,
  isLoading: false,
  sensorMode: 'normal' as const,
  isHudEnabled: true,
  isDetectionOverlay: true,
  isCockpitMode: false,
  followedMmsi: null,
  mapBase: 'dark' as const,
  wsConnected: false,

  fetchInitialData: async () => {
    set({ isLoading: true });
    try {
      const incidents = await api.fetchIncidents();
      const vessels = await api.fetchVessels();
      
      set({ incidents, vessels });
      await get().pollLiveVessels();

      if (incidents.length > 0) {
        await get().selectIncident(incidents[0]);
      }
    } catch (err) {
      console.error('Error fetching initial data:', err);
    } finally {
      set({ isLoading: false });
    }
  },

  pollLiveVessels: async () => {
    try {
      const liveData = await api.fetchLiveVessels();
      set({ liveVessels: liveData.vessels || [] });
    } catch (e) {
      console.error('Live vessel poll failed', e);
    }
  },

  selectIncident: async (incident: Incident) => {
    set({ activeIncident: incident, isLoading: true });
    try {
      const [segmentation, oceanDrift, attributionScores, evidenceItems] = await Promise.all([
        api.fetchSegmentation(incident.id),
        api.fetchOceanDrift(incident.id, incident.latitude, incident.longitude),
        api.fetchAttribution(incident.id),
        api.fetchEvidence(incident.id)
      ]);

      const topSelected = attributionScores.length > 0 ? attributionScores[0] : null;

      set({
        segmentation,
        oceanDrift,
        attributionScores,
        selectedAttribution: topSelected,
        evidenceItems,
        timeline: { ...get().timeline, currentTimeHoursAgo: 0.0 }
      });
    } catch (err) {
      console.error('Error fetching incident details:', err);
    } finally {
      set({ isLoading: false });
    }
  },

  selectVessel: (attribution) => {
    set({ selectedAttribution: attribution });
    if (attribution) {
      set({ activeInspectorTab: 'attribution' });
    }
  },

  toggleLayer: (layerName) => {
    set((state) => ({
      layers: {
        ...state.layers,
        [layerName]: !state.layers[layerName]
      }
    }));
  },

  setTimelineTime: (hoursAgo) => {
    set((state) => ({
      timeline: { ...state.timeline, currentTimeHoursAgo: hoursAgo }
    }));
  },

  togglePlayback: () => {
    set((state) => ({
      timeline: { ...state.timeline, isPlaying: !state.timeline.isPlaying }
    }));
  },

  setPlaybackSpeed: (speed) => {
    set((state) => ({
      timeline: { ...state.timeline, playbackSpeed: speed }
    }));
  },

  setActiveInspectorTab: (tab) => set({ activeInspectorTab: tab }),
  setReportModalOpen: (open) => set({ isReportModalOpen: open }),
  setIngestModalOpen: (open) => set({ isIngestModalOpen: open }),
  setHealthDrawerOpen: (open) => set({ isHealthDrawerOpen: open }),
  setSensorMode: (mode) => set({ sensorMode: mode }),
  setHudEnabled: (v) => set({ isHudEnabled: v }),
  setDetectionOverlay: (v) => set({ isDetectionOverlay: v }),
  setCockpitMode: (v, mmsi = null) => set({ isCockpitMode: v, followedMmsi: mmsi }),
  setMapBase: (base) => set({ mapBase: base }),
  setWsConnected: (v) => set({ wsConnected: v }),

  ingestNewScene: async (sceneId: string) => {
    set({ isLoading: true });
    try {
      await api.triggerSceneIngest(sceneId);
      const newInc = await api.createIncident({
        name: `Sentinel-1 Ingest (${sceneId})`,
        region: 'Strait of Malacca Sector 2',
        latitude: 1.285,
        longitude: 103.825
      });
      
      const incidents = await api.fetchIncidents();
      set({ incidents });
      await get().selectIncident(newInc);
    } catch (err) {
      console.error('Scene ingestion failed:', err);
    } finally {
      set({ isLoading: false });
    }
  }
}));
