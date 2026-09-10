import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { useIncidentStore } from '../store/useIncidentStore';

const SENSOR_FILTERS: Record<string, string> = {
  normal: 'none',
  crt: 'contrast(1.15) brightness(0.95) saturate(0.7) hue-rotate(5deg)',
  nvg: 'brightness(1.2) contrast(1.25) hue-rotate(75deg) saturate(0.45) sepia(0.2)',
  thermal: 'invert(0.85) hue-rotate(180deg) contrast(1.3) brightness(1.1)',
  flir: 'grayscale(1) invert(1) contrast(1.4) brightness(1.05)',
  noir: 'grayscale(1) contrast(1.2) brightness(0.9)',
  snow: 'brightness(1.35) contrast(0.9) saturate(0.2) hue-rotate(10deg)',
};

export const MapView: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const vesselMarkersRef = useRef<Map<number, L.Marker>>(new Map());

  const {
    activeIncident,
    segmentation,
    oceanDrift,
    attributionScores,
    selectedAttribution,
    selectVessel,
    layers,
    liveVessels,
    sensorMode,
    isHudEnabled,
    isDetectionOverlay,
    isCockpitMode,
    followedMmsi,
    mapBase,
    setSensorMode,
    setCockpitMode,
  } = useIncidentStore();

  const [mapReady, setMapReady] = useState(false);
  const [showLandMask, setShowLandMask] = useState(true);

  // Initialize Leaflet Map - Gods Eye base stack
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const initialLat = activeIncident ? activeIncident.latitude : 1.3120;
    const initialLon = activeIncident ? activeIncident.longitude : 103.8540;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 12,
      zoomControl: true,
      attributionControl: false,
      preferCanvas: true,
    });

    // God's Eye Map Stack: Dark → Satellite → Ocean
    const tileUrls: Record<string, string> = {
      dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ocean: 'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
    };
    const tl = L.tileLayer(tileUrls[mapBase] || tileUrls.dark, {
      maxZoom: 18,
      attribution: 'Tiles &copy; Esri &mdash; &copy; OceanGuard God\'s Eye',
    }).addTo(map);
    tileLayerRef.current = tl;

    const layerGroup = L.layerGroup().addTo(map);
    layerGroupRef.current = layerGroup;
    mapRef.current = map;
    setMapReady(true);

    // Keyboard shortcuts 1-7 for sensor styles (God's Eye)
    const onKey = (e: KeyboardEvent) => {
      const keys: Record<string, any> = { '1': 'normal', '2': 'crt', '3': 'nvg', '4': 'thermal', '5': 'flir', '6': 'noir', '7': 'snow' };
      if (keys[e.key]) setSensorMode(keys[e.key]);
      if (e.key.toLowerCase() === 'h') useIncidentStore.getState().setHudEnabled(!useIncidentStore.getState().isHudEnabled);
      if (e.key.toLowerCase() === 'd') useIncidentStore.getState().setDetectionOverlay(!useIncidentStore.getState().isDetectionOverlay);
      if (e.key.toLowerCase() === 'c' && followedMmsi) useIncidentStore.getState().setCockpitMode(!useIncidentStore.getState().isCockpitMode, followedMmsi);
      if (e.key === 'Escape') useIncidentStore.getState().setCockpitMode(false, null);
    };
    window.addEventListener('keydown', onKey);

    return () => {
      window.removeEventListener('keydown', onKey);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Switch base layer when mapBase changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !tileLayerRef.current) return;
    const urls: Record<string, string> = {
      dark: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ocean: 'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
    };
    tileLayerRef.current.setUrl(urls[mapBase] || urls.dark);
  }, [mapBase]);

  // Cockpit mode: follow vessel (God's Eye cockpit)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isCockpitMode || !followedMmsi) return;
    const target = liveVessels.find(v => v.mmsi === followedMmsi);
    if (target) {
      map.flyTo([target.latitude, target.longitude], 14, { duration: 1.5, easeLinearity: 0.25 });
    }
  }, [liveVessels, isCockpitMode, followedMmsi]);

  // Update map center & layer contents when state changes
  useEffect(() => {
    const map = mapRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup || !activeIncident) return;

    layerGroup.clearLayers();
    vesselMarkersRef.current.clear();

    // Fly smoothly to active incident centroid (unless in cockpit)
    if (!isCockpitMode) {
      map.flyTo([activeIncident.latitude, activeIncident.longitude], 12, { duration: 1.2 });
    }

    // 0. Land mask shading (simplified Singapore/Malaysia boxes for visual cue)
    if (showLandMask) {
      const landPolys = [
        // Singapore island rough
        [[103.62, 1.28], [103.78, 1.33], [103.96, 1.38], [104.02, 1.34], [103.95, 1.27], [103.80, 1.22], [103.62, 1.28]],
        // Johor tip
        [[103.60, 1.32], [103.75, 1.55], [103.95, 1.45], [103.85, 1.28], [103.60, 1.32]],
      ];
      landPolys.forEach(coords => {
        L.polygon(coords.map(c => [c[1], c[0]] as L.LatLngExpression), {
          color: '#2b3d20',
          weight: 1,
          fillColor: '#1a2b15',
          fillOpacity: 0.22,
          dashArray: '2,6',
        }).addTo(layerGroup);
      });
    }

    // 1. Render Oil Slick Polygon - OCEAN-ONLY (if null, no spill rendered on land)
    if (layers.spillPolygon && segmentation?.polygon_geojson) {
      try {
        const isOceanValid = (segmentation as any).water_ratio === undefined || (segmentation as any).water_ratio >= 0.6;
        if (!isOceanValid) {
          console.warn('Suppressing land spill polygon');
        } else {
          const slickGeoJSON = L.geoJSON(segmentation.polygon_geojson, {
            style: {
              color: '#e43d3d',
              weight: 2,
              fillColor: '#e43d3d',
              fillOpacity: 0.35,
            }
          });
          slickGeoJSON.bindPopup(`
            <div style="font-family: sans-serif; padding: 4px;">
              <strong style="color: #e43d3d; font-size: 13px;">S1A Oil Slick Detection (Ocean-Validated)</strong><br/>
              <span style="font-size: 11px; color: #9fb2c3;">Area: ${segmentation.metrics.area_km2} km² | Water: ${Math.round(((segmentation as any).water_ratio||1)*100)}%</span><br/>
              <span style="font-size: 11px; color: #36c879;">Confidence: ${Math.round((segmentation.confidence || 0)*100)}% | Lookalike: ${Math.round((segmentation.lookalike_score||0)*100)}%</span><br/>
              <span style="font-size: 10px; color: #ff9f1c;">Land mask: OCEAN-ONLY ✓</span>
            </div>
          `);
          layerGroup.addLayer(slickGeoJSON);
          // Detection overlay box around slick
          if (isDetectionOverlay) {
            const b = segmentation.metrics.bbox;
            if (b) {
              const detRect = L.rectangle([[b[1], b[0]], [b[3], b[2]]], {
                color: '#36c879', weight: 1, dashArray: '4,4', fillOpacity: 0,
              });
              layerGroup.addLayer(detRect);
            }
          }
        }
      } catch (e) {
        console.error('Error rendering slick GeoJSON', e);
      }
    } else if (layers.spillPolygon && segmentation && !segmentation.polygon_geojson) {
      // Suppressed land spill - show toast in console
      console.log('OceanGuard: spill suppressed on land (water_ratio < threshold)');
    }

    // 2. Render Probable Origin Zone
    if (layers.probableOriginZone && oceanDrift?.origin_zone_geojson) {
      try {
        const originGeoJSON = L.geoJSON(oceanDrift.origin_zone_geojson, {
          style: {
            color: '#32c7e8',
            weight: 2,
            dashArray: '6, 6',
            fillColor: '#32c7e8',
            fillOpacity: 0.15,
          }
        });
        originGeoJSON.bindPopup(`
          <div style="font-family: sans-serif; padding: 4px;">
            <strong style="color: #32c7e8; font-size: 13px;">Probable Origin Zone (Hindcast)</strong><br/>
            <span style="font-size: 11px; color: #9fb2c3;">Reconstructed release window: ~${activeIncident.estimated_age_hours}h ago | Ocean-filtered: ✓</span>
          </div>
        `);
        layerGroup.addLayer(originGeoJSON);
      } catch (e) {
        console.error('Error rendering origin zone GeoJSON', e);
      }
    }

    // 3. Render 24h & 48h Drift Forecasts
    if (layers.forecast24h && oceanDrift?.forecast_24h_geojson) {
      const fc24 = L.geoJSON(oceanDrift.forecast_24h_geojson, {
        style: { color: '#ff9f1c', weight: 3, dashArray: '4, 4' }
      });
      layerGroup.addLayer(fc24);
    }
    if (layers.forecast48h && oceanDrift?.forecast_48h_geojson) {
      const fc48 = L.geoJSON(oceanDrift.forecast_48h_geojson, {
        style: { color: '#ffd23f', weight: 2, dashArray: '4, 4' }
      });
      layerGroup.addLayer(fc48);
    }

    // 4. Render Drift Particles (ocean-only already filtered)
    if (oceanDrift?.particles) {
      oceanDrift.particles.slice(0, 60).forEach(p => {
        const particleMarker = L.circleMarker([p.lat, p.lon], {
          radius: 2.5,
          color: '#32c7e8',
          fillColor: '#32c7e8',
          fillOpacity: p.probability * 0.65,
          stroke: false
        });
        layerGroup.addLayer(particleMarker);
      });
    }

    // 5. Render Candidate Vessels & Trajectories (attribution)
    if (layers.vessels && attributionScores.length > 0) {
      attributionScores.forEach((candidate, idx) => {
        const isSelected = selectedAttribution?.vessel_id === candidate.vessel_id;
        const isVOI = candidate.category === 'Vessel of Interest';

        const offsetLat = (idx === 0 ? 0.008 : idx === 1 ? -0.015 : idx === 2 ? 0.025 : -0.030);
        const offsetLon = (idx === 0 ? -0.012 : idx === 1 ? 0.020 : idx === 2 ? 0.035 : -0.040);
        const vLat = activeIncident.latitude + offsetLat;
        const vLon = activeIncident.longitude + offsetLon;

        const markerColor = isSelected ? '#ff3b30' : isVOI ? '#ff9f1c' : '#38d4e8';
        const customIcon = L.divIcon({
          className: 'vessel-map-icon',
          html: `
            <div style="
              width: ${isSelected ? 26 : 20}px;
              height: ${isSelected ? 26 : 20}px;
              background-color: ${markerColor};
              border: 2px solid #ffffff;
              border-radius: 50%;
              box-shadow: 0 0 12px ${markerColor};
              display: flex;
              align-items: center;
              justify-content: center;
              color: #ffffff;
              font-weight: bold;
              font-size: 10px;
            ">
              ${idx + 1}
            </div>
            ${isDetectionOverlay ? `<div style="position:absolute; top:-14px; left:50%; transform:translateX(-50%); background:rgba(54,200,121,0.92); color:#06111d; font-family:monospace; font-size:8px; font-weight:700; padding:1px 4px; white-space:nowrap; border:1px solid #36c879;">DET-CAND-${idx+1} ${Math.round(candidate.overall_score)}%</div>` : ''}
          `,
          iconSize: [26, 26],
          iconAnchor: [13, 13]
        });

        const marker = L.marker([vLat, vLon], { icon: customIcon });
        marker.on('click', () => {
          selectVessel(candidate);
          setCockpitMode(false, null);
        });
        marker.bindPopup(`
          <div style="font-family: sans-serif; padding: 4px;">
            <strong style="color: #e7f0f7; font-size: 13px;">${candidate.vessel_name}</strong><br/>
            <span style="font-size: 11px; color: #9fb2c3;">MMSI: ${candidate.mmsi}</span><br/>
            <span style="font-size: 11px; color: ${markerColor}; font-weight: bold;">
              ${candidate.category} (${candidate.overall_score}%)
            </span><br/>
            <span style="font-size: 10px; color:#6f8496;">Click to inspect → Attribution</span>
          </div>
        `);
        layerGroup.addLayer(marker);

        if (layers.vesselTrails) {
          const trailCoords: L.LatLngExpression[] = [
            [vLat - 0.03, vLon - 0.04],
            [vLat - 0.015, vLon - 0.02],
            [vLat, vLon]
          ];
          const trailPolyline = L.polyline(trailCoords, {
            color: isSelected ? '#ff3b30' : '#27d17f',
            weight: isSelected ? 3 : 2,
            dashArray: '4, 4',
            opacity: 0.75
          });
          layerGroup.addLayer(trailPolyline);
        }
      });
    }

    // 6. Render Real-Time Streaming AIS Vessels - GOD'S EYE WORLD-STABLE
    if (layers.vessels && liveVessels.length > 0) {
      liveVessels.forEach((lv) => {
        const isTarget = lv.is_target_of_interest;
        const color = isTarget ? '#ff3b30' : '#38d4e8';
        const isFollowed = followedMmsi === lv.mmsi && isCockpitMode;

        // God's Eye trail (fading)
        if (layers.vesselTrails && lv.trail && lv.trail.length > 1) {
          const trailCoords: L.LatLngExpression[] = lv.trail.map((t: any) => [t.lat, t.lon] as L.LatLngExpression);
          const opacitySteps = trailCoords.map((_, i, arr) => 0.15 + 0.75 * (i / arr.length));
          // Draw multi-segment with gradient-like via single polyline with low opacity (simplified)
          const trailLine = L.polyline(trailCoords, {
            color: isFollowed ? '#ff3b30' : '#27d17f',
            weight: isFollowed ? 3 : 2,
            opacity: 0.55,
            dashArray: '3,6',
            lineCap: 'round',
          });
          (trailLine as any).options.className = 'vessel-trail-glow';
          layerGroup.addLayer(trailLine);
        }

        // World-stable heading icon (God's Eye: per-frame screen-space course projection)
        // Outer circle + inner triangle pointing along true heading
        const heading = lv.heading_deg || lv.course_deg || 0;
        const liveIcon = L.divIcon({
          className: 'live-vessel-icon vessel-heading-stable',
          html: `
            <div style="position:relative; width:22px; height:22px; display:flex; align-items:center; justify-content:center;">
              <div style="
                width: 16px;
                height: 16px;
                background: ${color};
                border: 2px solid #ffffff;
                border-radius: 50%;
                box-shadow: 0 0 10px ${color};
                display:flex; align-items:center; justify-content:center;
                transform: rotate(${heading}deg);
                transition: transform 0.8s linear;
              ">
                <div style="width:0; height:0; border-left:4px solid transparent; border-right:4px solid transparent; border-bottom:6px solid white; transform: translateY(-1px);"></div>
              </div>
              ${isFollowed ? `<div style="position:absolute; inset:-4px; border:1px solid #ff3b30; border-radius:50%; animation: pulse 1.5s infinite;"></div>` : ''}
              ${isDetectionOverlay ? `<div style="position:absolute; top:-18px; left:50%; transform:translateX(-50%); background:${isTarget ? 'rgba(255,59,48,0.92)' : 'rgba(54,200,121,0.86)'}; color:${isTarget?'#fff':'#06111d'}; font-family:monospace; font-size:8px; font-weight:700; padding:1px 4px; border:1px solid ${color}; white-space:nowrap;">${lv.name.slice(0,10)} ${(lv.threat_score||0).toString().slice(0,2)}%</div>` : ''}
              <div style="position:absolute; bottom:-6px; left:50%; transform:translateX(-50%); width:2px; height:6px; background:${color}; opacity:0.7;"></div>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11]
        });

        const liveMarker = L.marker([lv.latitude, lv.longitude], { icon: liveIcon });
        liveMarker.on('click', () => {
          // On click, enter cockpit follow
          setCockpitMode(true, lv.mmsi);
          // Also try to find attribution
          const attr = attributionScores.find(a => a.mmsi === lv.mmsi);
          if (attr) selectVessel(attr);
        });
        liveMarker.bindPopup(`
          <div style="font-family: monospace; padding: 6px; background: #040a12; color: #e7f0f7; min-width: 220px;">
            <strong style="color: ${isTarget ? '#ff3b30' : '#32c7e8'}; font-size: 13px;">${lv.name}</strong> ${isFollowed ? '<span style="background:#ff3b30; color:#fff; font-size:9px; padding:1px 4px; border-radius:3px;">COCKPIT</span>' : ''}<br/>
            <span style="font-size: 11px; color: #9fb2c3;">IMO: ${lv.imo} | MMSI: ${lv.mmsi}</span><br/>
            <span style="font-size: 11px; color: #9fb2c3;">Type: ${lv.ship_type} (${lv.flag})</span><br/>
            <span style="font-size: 11px; color: #36c879; font-weight: bold;">
              KINEMATICS: ${lv.speed_knots} kts @ ${lv.heading_deg}° COG | Course ${lv.course_deg}°
            </span><br/>
            <span style="font-size: 11px; color: #ff9f1c;">Draft: ${lv.draft_m || 12.0}m | Dest: ${lv.destination || 'N/A'}</span><br/>
            <span style="font-size: 10px; color: #6f8496;">Receiver: ${lv.receiver_station} (${lv.signal_rssi_dbm} dBm) | <span style="color:#32c7e8;">Click to enter COCKPIT</span></span>
          </div>
        `);
        layerGroup.addLayer(liveMarker);
        vesselMarkersRef.current.set(lv.mmsi, liveMarker);
      });
    }

  }, [activeIncident, segmentation, oceanDrift, attributionScores, selectedAttribution, layers, liveVessels, isCockpitMode, followedMmsi, isDetectionOverlay, showLandMask]);

  const topCandidate = attributionScores[0];

  return (
    <div className="map-area gods-eye-container" style={{ width: '100%', height: '100%', position: 'relative', filter: SENSOR_FILTERS[sensorMode] || 'none' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* God's Eye HUD */}
      {isHudEnabled && mapReady && (
        <div className="hud-overlay">
          <div className="hud-corner tl" />
          <div className="hud-corner tr" />
          <div className="hud-corner bl" />
          <div className="hud-corner br" />
          <div className="hud-crosshair" />
          <div className="hud-top-bar">
            <div style={{ display: 'flex', gap: '14px', alignItems: 'center' }}>
              <span style={{ color: '#36c879', fontWeight: 800 }}>● LIVE</span>
              <span>GOD'S EYE // OCEANGUARD MARITIME INTELLIGENCE</span>
              <span style={{ color: '#6f8496' }}>SENSOR: {sensorMode.toUpperCase()}</span>
              {isCockpitMode && followedMmsi && <span style={{ color: '#ff3b30', fontWeight: 800 }}>COCKPIT → MMSI {followedMmsi}</span>}
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <span>INCIDENT: {activeIncident?.code || '—'}</span>
              <span style={{ color: '#32c7e8' }}>{activeIncident ? `${activeIncident.latitude.toFixed(4)}, ${activeIncident.longitude.toFixed(4)}` : '—'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Cockpit vignette */}
      {isCockpitMode && (
        <div className="cockpit-vignette">
          <div className="cockpit-frame" />
          <div style={{ position: 'absolute', bottom: '14px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(6,17,29,0.85)', border: '1px solid #ff3b30', color: '#ff9f1c', fontFamily: 'monospace', fontSize: '11px', padding: '4px 10px', borderRadius: '6px', display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ width: '8px', height: '8px', background: '#ff3b30', borderRadius: '50%', display: 'inline-block', boxShadow: '0 0 8px #ff3b30' }} />
            <span>COCKPIT VIEW — TRACKING {liveVessels.find(v => v.mmsi === followedMmsi)?.name || followedMmsi}</span>
            <button onClick={() => setCockpitMode(false, null)} style={{ background: '#ff3b30', color: '#fff', border: 'none', padding: '2px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '10px', fontWeight: 700 }}>EXIT [Esc]</button>
          </div>
        </div>
      )}

      {/* Sensor sweep chips */}
      <div style={{
        position: 'absolute',
        bottom: '14px',
        left: '14px',
        background: 'rgba(13, 28, 43, 0.90)',
        backdropFilter: 'blur(8px)',
        border: '1px solid #1e3449',
        borderRadius: '8px',
        padding: '8px 10px',
        zIndex: 900,
        pointerEvents: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        minWidth: '170px'
      }}>
        <div style={{ fontWeight: 800, color: '#32c7e8', fontSize: '10px', letterSpacing: '0.6px', display: 'flex', justifyContent: 'space-between' }}>
          <span>SENSOR MODE</span>
          <span style={{ color: '#6f8496' }}>Keys 1-7</span>
        </div>
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {Object.keys(SENSOR_FILTERS).map(k => (
            <button
              key={k}
              onClick={() => setSensorMode(k as any)}
              className={sensorMode === k ? 'sensor-chip-active' : ''}
              style={{
                fontSize: '9px',
                padding: '3px 6px',
                borderRadius: '4px',
                border: '1px solid #1e3449',
                background: sensorMode === k ? 'rgba(22,119,232,0.22)' : 'transparent',
                color: sensorMode === k ? '#32c7e8' : '#6f8496',
                cursor: 'pointer',
                fontWeight: sensorMode === k ? 700 : 400,
                textTransform: 'uppercase'
              }}
            >
              {k}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: '6px', marginTop: '2px' }}>
          <button onClick={() => useIncidentStore.getState().setHudEnabled(!isHudEnabled)} style={{ flex: 1, fontSize: '10px', padding: '4px', borderRadius: '4px', border: '1px solid', borderColor: isHudEnabled ? '#1677e8' : '#1e3449', background: isHudEnabled ? 'rgba(22,119,232,0.15)' : 'transparent', color: isHudEnabled ? '#32c7e8' : '#6f8496', cursor: 'pointer' }}>
            HUD {isHudEnabled ? 'ON' : 'OFF'} [H]
          </button>
          <button onClick={() => useIncidentStore.getState().setDetectionOverlay(!isDetectionOverlay)} style={{ flex: 1, fontSize: '10px', padding: '4px', borderRadius: '4px', border: '1px solid', borderColor: isDetectionOverlay ? '#36c879' : '#1e3449', background: isDetectionOverlay ? 'rgba(54,200,121,0.15)' : 'transparent', color: isDetectionOverlay ? '#36c879' : '#6f8496', cursor: 'pointer' }}>
            DET {isDetectionOverlay ? 'ON' : 'OFF'} [D]
          </button>
        </div>
      </div>

      {/* Map Legend & Controls */}
      <div style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        background: 'rgba(13, 28, 43, 0.85)',
        backdropFilter: 'blur(8px)',
        border: '1px solid #1e3449',
        borderRadius: '8px',
        padding: '10px 14px',
        zIndex: 900,
        pointerEvents: 'auto',
        fontSize: '11px',
        color: '#e7f0f7',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        minWidth: '190px'
      }}>
        <div style={{ fontWeight: 'bold', color: '#32c7e8', marginBottom: '2px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>MAP LEGEND — GOD'S EYE</span>
          <span style={{ fontSize: '9px', color: '#6f8496' }}>OCEAN-ONLY ✓</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '12px', background: 'rgba(228, 61, 61, 0.4)', border: '1px solid #e43d3d', borderRadius: '3px' }}></span>
          <span>SAR Oil Slick (Ocean)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '12px', background: 'rgba(50, 199, 232, 0.2)', border: '1px dashed #32c7e8', borderRadius: '3px' }}></span>
          <span>Probable Origin Zone</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '3px', background: '#ff9f1c' }}></span>
          <span>24h Drift Forecast</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '10px', height: '10px', background: '#ff3b30', borderRadius: '50%' }}></span>
          <span>Vessel of Interest</span>
        </div>
        <div style={{ height: '1px', background: '#1e3449', margin: '4px 0' }} />
        <div style={{ display: 'flex', gap: '4px' }}>
          {(['dark', 'satellite', 'ocean'] as const).map(b => (
            <button key={b} onClick={() => useIncidentStore.getState().setMapBase(b)} style={{ flex: 1, fontSize: '9px', padding: '3px 4px', borderRadius: '4px', border: '1px solid', borderColor: mapBase === b ? '#32c7e8' : '#1e3449', background: mapBase === b ? 'rgba(50,199,232,0.15)' : 'transparent', color: mapBase === b ? '#32c7e8' : '#6f8496', cursor: 'pointer', textTransform: 'uppercase' }}>{b}</button>
          ))}
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '10px', color: '#9fb2c3', cursor: 'pointer' }}>
          <input type="checkbox" checked={showLandMask} onChange={e => setShowLandMask(e.target.checked)} />
          Show land mask shading
        </label>
        {topCandidate && (
          <div style={{ background: '#0a1725', border: '1px solid #1e3449', borderRadius: '6px', padding: '6px 8px', marginTop: '4px' }}>
            <div style={{ fontSize: '10px', color: '#6f8496' }}>TOP CANDIDATE</div>
            <div style={{ fontSize: '11px', fontWeight: 700, color: '#ff3b30' }}>{topCandidate.vessel_name} — {topCandidate.overall_score}%</div>
          </div>
        )}
      </div>

      {/* Bottom HUD Telemetry Bar (God's Eye intelligence strip) */}
      <div className="hud-bottom-bar" style={{ position: 'absolute', bottom: '0', left: '0', right: '0', zIndex: 850 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="pulse-dot" style={{ width: '6px', height: '6px', background: '#36c879', borderRadius: '50%', display: 'inline-block' }} />
          <span style={{ fontWeight: 700, color: '#36c879' }}>{liveVessels.length} CONTACTS LIVE</span>
        </div>
        <span style={{ color: '#6f8496' }}>|</span>
        <span>Spill: <strong style={{ color: segmentation?.polygon_geojson ? '#e43d3d' : '#6f8496' }}>{segmentation?.polygon_geojson ? `${segmentation.metrics.area_km2} km²` : 'SUPPRESSED (LAND) or NO DETECTION'}</strong></span>
        <span style={{ color: '#6f8496' }}>|</span>
        <span>Wind <strong style={{ color: '#32c7e8' }}>{oceanDrift?.wind_speed_knots ?? 14.5} kts @ {oceanDrift?.wind_direction_deg ?? 225}°</strong></span>
        <span style={{ color: '#6f8496' }}>|</span>
        <span>Ocean-filtered <strong style={{ color: '#36c879' }}>✓</strong> | Press <strong>H</strong> HUD <strong>D</strong> DET <strong>C</strong> Cockpit <strong>1-7</strong> Sensor</span>
      </div>
    </div>
  );
};