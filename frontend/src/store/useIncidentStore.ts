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

  // REAL ML RESULT
  segmentation: SegmentationResult | null;

  oceanDrift: OceanDriftResult | null;
  vessels: Vessel[];
  liveVessels: any[];

  attributionScores: AttributionScore[];
  selectedAttribution: AttributionScore | null;

  evidenceItems: EvidenceItem[];

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

  timeline: {
    currentTimeHoursAgo: number;
    isPlaying: boolean;
    playbackSpeed: number;
  };

  activeInspectorTab: 'spill' | 'vessels' | 'attribution' | 'evidence';

  isReportModalOpen: boolean;
  isIngestModalOpen: boolean;
  isHealthDrawerOpen: boolean;

  isLoading: boolean;

  fetchInitialData: () => Promise<void>;
  pollLiveVessels: () => Promise<void>;

  selectIncident: (incident: Incident) => Promise<void>;

  selectVessel: (
    attribution: AttributionScore | null
  ) => void;

  toggleLayer: (
    layerName: keyof IncidentState['layers']
  ) => void;

  setTimelineTime: (hoursAgo: number) => void;

  togglePlayback: () => void;

  setPlaybackSpeed: (speed: number) => void;

  setActiveInspectorTab: (
    tab: IncidentState['activeInspectorTab']
  ) => void;

  setReportModalOpen: (open: boolean) => void;

  setIngestModalOpen: (open: boolean) => void;

  setHealthDrawerOpen: (open: boolean) => void;

  ingestNewScene: (sceneId: string) => Promise<void>;
}

export const useIncidentStore = create<IncidentState>((set, get) => ({
  incidents: [],

  activeIncident: null,

  // IMPORTANT:
  // This is where REAL ML segmentation result is stored.
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
    sarOverlay: true
  },

  timeline: {
    currentTimeHoursAgo: 0.0,
    isPlaying: false,
    playbackSpeed: 1
  },

  activeInspectorTab: 'vessels',

  isReportModalOpen: false,

  isIngestModalOpen: false,

  isHealthDrawerOpen: false,

  isLoading: false,

  // ============================================================
  // INITIAL DATA
  // ============================================================

  fetchInitialData: async () => {
    console.log('🔵 Fetching initial incidents...');

    set({
      isLoading: true
    });

    try {
      const incidents = await api.fetchIncidents();

      console.log(
        '✅ Incidents loaded:',
        incidents
      );

      const vessels = await api.fetchVessels();

      console.log(
        '✅ Vessels loaded:',
        vessels
      );

      set({
        incidents,
        vessels
      });

      await get().pollLiveVessels();

      if (incidents.length > 0) {
        console.log(
          '🔵 Selecting first incident:',
          incidents[0].id
        );

        await get().selectIncident(
          incidents[0]
        );
      }

    } catch (err) {

      console.error(
        '❌ Error fetching initial data:',
        err
      );

    } finally {

      set({
        isLoading: false
      });
    }
  },

  // ============================================================
  // LIVE AIS
  // ============================================================

  pollLiveVessels: async () => {

    try {

      const liveData =
        await api.fetchLiveVessels();

      set({
        liveVessels:
          liveData?.vessels || []
      });

    } catch (err) {

      console.error(
        '❌ Live vessel poll failed:',
        err
      );
    }
  },

  // ============================================================
  // SELECT INCIDENT
  // ============================================================

  selectIncident: async (
    incident: Incident
  ) => {

    console.log(
      '🔵 Selecting incident:',
      incident.id
    );

    // Immediately change selected incident.
    set({
      activeIncident: incident,

      // Clear old ML result so UI does not display
      // previous incident's segmentation.
      segmentation: null,

      oceanDrift: null,

      attributionScores: [],

      selectedAttribution: null,

      evidenceItems: [],

      isLoading: true
    });

    try {

      // --------------------------------------------------------
      // Run all services independently.
      //
      // This is important because one service failure
      // should NOT prevent ML segmentation from appearing.
      // --------------------------------------------------------

      const results =
        await Promise.allSettled([

          // INDEX 0 = REAL ML
          api.fetchSegmentation(
            incident.id
          ),

          // INDEX 1 = OCEAN
          api.fetchOceanDrift(
            incident.id,
            incident.latitude,
            incident.longitude
          ),

          // INDEX 2 = ATTRIBUTION
          api.fetchAttribution(
            incident.id
          ),

          // INDEX 3 = EVIDENCE
          api.fetchEvidence(
            incident.id
          )
        ]);

      // ========================================================
      // REAL ML SEGMENTATION
      // ========================================================

      const segmentationResult =
        results[0];

      if (
        segmentationResult.status ===
        'fulfilled'
      ) {

        const segmentation =
          segmentationResult.value;

        console.log(
          '================================'
        );

        console.log(
          '✅ REAL ML SEGMENTATION LOADED'
        );

        console.log(
          'ML confidence:',
          segmentation.confidence
        );

        console.log(
          'Oil spill:',
          segmentation.is_spill
        );

        console.log(
          'Oil area:',
          segmentation.metrics.area_km2,
          'km²'
        );

        console.log(
          'Look-alike score:',
          segmentation.lookalike_score
        );

        console.log(
          'Polygon:',
          segmentation.polygon_geojson
        );

        console.log(
          '================================'
        );

        // THIS IS THE IMPORTANT PART
        // Push the REAL ML result into Zustand.
        set({
          segmentation
        });

      } else {

        console.error(
          '❌ Segmentation failed:',
          segmentationResult.reason
        );

        // Keep segmentation null.
        set({
          segmentation: null
        });
      }

      // ========================================================
      // OCEAN DRIFT
      // ========================================================

      const oceanResult =
        results[1];

      if (
        oceanResult.status ===
        'fulfilled'
      ) {

        console.log(
          '✅ Ocean drift loaded'
        );

        set({
          oceanDrift:
            oceanResult.value
        });

      } else {

        console.error(
          '❌ Ocean drift failed:',
          oceanResult.reason
        );
      }

      // ========================================================
      // ATTRIBUTION
      // ========================================================

      const attributionResult =
        results[2];

      if (
        attributionResult.status ===
        'fulfilled'
      ) {

        const attributionScores =
          attributionResult.value;

        console.log(
          '✅ Attribution loaded:',
          attributionScores
        );

        const topSelected =
          attributionScores.length > 0
            ? attributionScores[0]
            : null;

        set({
          attributionScores,
          selectedAttribution:
            topSelected
        });

      } else {

        console.error(
          '❌ Attribution failed:',
          attributionResult.reason
        );
      }

      // ========================================================
      // EVIDENCE
      // ========================================================

      const evidenceResult =
        results[3];

      if (
        evidenceResult.status ===
        'fulfilled'
      ) {

        console.log(
          '✅ Evidence loaded'
        );

        set({
          evidenceItems:
            evidenceResult.value
        });

      } else {

        console.error(
          '❌ Evidence failed:',
          evidenceResult.reason
        );
      }

      // ========================================================
      // RESET TIMELINE
      // ========================================================

      set({
        timeline: {
          ...get().timeline,
          currentTimeHoursAgo: 0
        }
      });

    } catch (err) {

      console.error(
        '❌ Unexpected incident error:',
        err
      );

    } finally {

      set({
        isLoading: false
      });
    }
  },

  // ============================================================
  // SELECT VESSEL
  // ============================================================

  selectVessel: (
    attribution
  ) => {

    set({
      selectedAttribution:
        attribution
    });

    if (attribution) {

      set({
        activeInspectorTab:
          'attribution'
      });
    }
  },

  // ============================================================
  // LAYERS
  // ============================================================

  toggleLayer: (
    layerName
  ) => {

    set((state) => ({
      layers: {
        ...state.layers,

        [layerName]:
          !state.layers[layerName]
      }
    }));
  },

  // ============================================================
  // TIMELINE
  // ============================================================

  setTimelineTime: (
    hoursAgo
  ) => {

    set((state) => ({
      timeline: {
        ...state.timeline,
        currentTimeHoursAgo:
          hoursAgo
      }
    }));
  },

  togglePlayback: () => {

    set((state) => ({
      timeline: {
        ...state.timeline,

        isPlaying:
          !state.timeline.isPlaying
      }
    }));
  },

  setPlaybackSpeed: (
    speed
  ) => {

    set((state) => ({
      timeline: {
        ...state.timeline,

        playbackSpeed:
          speed
      }
    }));
  },

  // ============================================================
  // UI
  // ============================================================

  setActiveInspectorTab: (
    tab
  ) => {

    set({
      activeInspectorTab:
        tab
    });
  },

  setReportModalOpen: (
    open
  ) => {

    set({
      isReportModalOpen:
        open
    });
  },

  setIngestModalOpen: (
    open
  ) => {

    set({
      isIngestModalOpen:
        open
    });
  },

  setHealthDrawerOpen: (
    open
  ) => {

    set({
      isHealthDrawerOpen:
        open
    });
  },

  // ============================================================
  // INGEST NEW SCENE
  // ============================================================

  ingestNewScene: async (
    sceneId: string
  ) => {

    console.log(
      '🔵 Ingesting scene:',
      sceneId
    );

    set({
      isLoading: true
    });

    try {

      await api.triggerSceneIngest(
        sceneId
      );

      console.log(
        '✅ Scene ingestion completed'
      );

      const newIncident =
        await api.createIncident({

          name:
            `Sentinel-1 Ingest (${sceneId})`,

          region:
            'Strait of Malacca Sector 2',

          latitude:
            1.285,

          longitude:
            103.825
        });

      console.log(
        '✅ New incident created:',
        newIncident
      );

      const incidents =
        await api.fetchIncidents();

      set({
        incidents
      });

      // Immediately run REAL ML on new incident.
      await get().selectIncident(
        newIncident
      );

    } catch (err) {

      console.error(
        '❌ Scene ingestion failed:',
        err
      );

    } finally {

      set({
        isLoading: false
      });
    }
  }
}));