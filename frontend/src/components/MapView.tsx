import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useIncidentStore } from '../store/useIncidentStore';

export const MapView: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  const {
    activeIncident,
    segmentation,
    oceanDrift,
    attributionScores,
    selectedAttribution,
    selectVessel,
    layers,
    liveVessels
  } = useIncidentStore();

  // ---------------------------------------------------------------
  // Initialize Leaflet Map
  // ---------------------------------------------------------------

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const initialLat = activeIncident
      ? activeIncident.latitude
      : 1.3120;

    const initialLon = activeIncident
      ? activeIncident.longitude
      : 103.8540;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 12,
      zoomControl: true,
      attributionControl: false
    });

    // Dark Ocean Base Layer
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 16,
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
      }
    ).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);

    layerGroupRef.current = layerGroup;
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      layerGroupRef.current = null;
    };
  }, []);
  // ---------------------------------------------------------------
  // MOVE MAP WHEN INCIDENT CHANGES
  // ---------------------------------------------------------------

  useEffect(() => {
    const map = mapRef.current;

    if (!map || !activeIncident) return;

    /*
     * First move to the selected incident.
     *
     * We intentionally use the INCIDENT coordinates here rather
     * than the ML centroid because every incident may eventually
     * have a different satellite image.
     */
    map.flyTo(
      [
        activeIncident.latitude,
        activeIncident.longitude
      ],
      12,
      {
        animate: true,
        duration: 0.8
      }
    );

  }, [activeIncident?.id]);

  // ---------------------------------------------------------------
  // Render map layers
  // ---------------------------------------------------------------

  useEffect(() => {
    const map = mapRef.current;
    const layerGroup = layerGroupRef.current;

    if (!map || !layerGroup || !activeIncident) return;

    layerGroup.clearLayers();

    // -------------------------------------------------------------
    // 1. Render REAL ML Oil Slick Polygon
    // -------------------------------------------------------------

    if (
      layers.spillPolygon &&
      segmentation?.polygon_geojson
    ) {
      try {
        const slickGeoJSON = L.geoJSON(
          segmentation.polygon_geojson,
          {
            style: {
              color: '#e43d3d',
              weight: 3,
              fillColor: '#e43d3d',
              fillOpacity: 0.45,
            }
          }
        );

        slickGeoJSON.bindPopup(`
          <div style="
            font-family: sans-serif;
            padding: 6px;
            min-width: 180px;
          ">
            <strong style="
              color: #e43d3d;
              font-size: 14px;
            ">
              REAL SAR OIL SPILL DETECTION
            </strong>

            <br/><br/>

            <span style="font-size: 11px; color: #9fb2c3;">
              Incident:
            </span>

            <strong style="font-size: 11px; color: #e7f0f7;">
              ${activeIncident.code}
            </strong>

            <br/>

            <span style="font-size: 11px; color: #9fb2c3;">
              Area:
            </span>

            <strong style="font-size: 11px; color: #e7f0f7;">
              ${segmentation.metrics.area_km2} km²
            </strong>

            <br/>

            <span style="font-size: 11px; color: #9fb2c3;">
              Perimeter:
            </span>

            <strong style="font-size: 11px; color: #e7f0f7;">
              ${segmentation.metrics.perimeter_km} km
            </strong>

            <br/>

            <span style="font-size: 11px; color: #9fb2c3;">
              Confidence:
            </span>

            <strong style="font-size: 11px; color: #36c879;">
              ${Math.round(segmentation.confidence * 100)}%
            </strong>

            <br/>

            <span style="font-size: 11px; color: #9fb2c3;">
              Look-alike:
            </span>

            <strong style="font-size: 11px; color: #ff9f1c;">
              ${Math.round(segmentation.lookalike_score * 100)}%
            </strong>

            <br/><br/>

            <span style="font-size: 10px; color: #6f8496;">
              Centroid:
              ${segmentation.metrics.centroid_lat.toFixed(6)},
              ${segmentation.metrics.centroid_lon.toFixed(6)}
            </span>
          </div>
        `);

        layerGroup.addLayer(slickGeoJSON);

        // ---------------------------------------------------------
        // REAL ML CENTROID MARKER
        // ---------------------------------------------------------

        const centroidMarker = L.circleMarker(
          [
            segmentation.metrics.centroid_lat,
            segmentation.metrics.centroid_lon
          ],
          {
            radius: 7,
            color: '#ffffff',
            weight: 2,
            fillColor: '#e43d3d',
            fillOpacity: 1,
          }
        );

        centroidMarker.bindPopup(`
          <div style="
            font-family: sans-serif;
            padding: 5px;
          ">
            <strong style="
              color: #e43d3d;
              font-size: 13px;
            ">
              ML DETECTED OIL CENTROID
            </strong>

            <br/><br/>

            <span style="font-size: 11px;">
              Incident:
              ${activeIncident.code}
            </span>

            <br/>

            <span style="font-size: 11px;">
              Lat:
              ${segmentation.metrics.centroid_lat.toFixed(6)}
            </span>

            <br/>

            <span style="font-size: 11px;">
              Lon:
              ${segmentation.metrics.centroid_lon.toFixed(6)}
            </span>
          </div>
        `);

        layerGroup.addLayer(centroidMarker);

      } catch (e) {
        console.error(
          'Error rendering slick GeoJSON:',
          e
        );
      }
    }

    // -------------------------------------------------------------
    // 2. Render Probable Origin Zone
    // -------------------------------------------------------------

    if (
      layers.probableOriginZone &&
      oceanDrift?.origin_zone_geojson
    ) {
      try {
        const originGeoJSON = L.geoJSON(
          oceanDrift.origin_zone_geojson,
          {
            style: {
              color: '#32c7e8',
              weight: 2,
              dashArray: '6, 6',
              fillColor: '#32c7e8',
              fillOpacity: 0.15,
            }
          }
        );

        originGeoJSON.bindPopup(`
          <div style="
            font-family: sans-serif;
            padding: 4px;
          ">
            <strong style="
              color: #32c7e8;
              font-size: 13px;
            ">
              Probable Origin Zone
            </strong>

            <br/>

            <span style="
              font-size: 11px;
              color: #9fb2c3;
            ">
              Incident:
              ${activeIncident.code}
            </span>

            <br/>

            <span style="
              font-size: 11px;
              color: #9fb2c3;
            ">
              Reconstructed release window:
              ~${activeIncident.estimated_age_hours}h ago
            </span>
          </div>
        `);

        layerGroup.addLayer(originGeoJSON);

      } catch (e) {
        console.error(
          'Error rendering origin zone GeoJSON:',
          e
        );
      }
    }

    // -------------------------------------------------------------
    // 3. Render 24h & 48h Drift Forecasts
    // -------------------------------------------------------------

    if (
      layers.forecast24h &&
      oceanDrift?.forecast_24h_geojson
    ) {
      const fc24 = L.geoJSON(
        oceanDrift.forecast_24h_geojson,
        {
          style: {
            color: '#ff9f1c',
            weight: 3,
            dashArray: '4, 4'
          }
        }
      );

      layerGroup.addLayer(fc24);
    }

    if (
      layers.forecast48h &&
      oceanDrift?.forecast_48h_geojson
    ) {
      const fc48 = L.geoJSON(
        oceanDrift.forecast_48h_geojson,
        {
          style: {
            color: '#ffd23f',
            weight: 2,
            dashArray: '4, 4'
          }
        }
      );

      layerGroup.addLayer(fc48);
    }

    // -------------------------------------------------------------
    // 4. Render Drift Particles
    // -------------------------------------------------------------

    if (oceanDrift?.particles) {

      oceanDrift.particles
        .slice(0, 40)
        .forEach((p) => {

          const particleMarker = L.circleMarker(
            [p.lat, p.lon],
            {
              radius: 3,
              color: '#32c7e8',
              fillColor: '#32c7e8',
              fillOpacity: p.probability * 0.6,
              stroke: false
            }
          );

          layerGroup.addLayer(
            particleMarker
          );
        });
    }

    // -------------------------------------------------------------
    // 5. Render Candidate Vessels & Trajectories
    // -------------------------------------------------------------

    if (
      layers.vessels &&
      attributionScores.length > 0
    ) {

      attributionScores.forEach(
        (candidate, idx) => {

          const isSelected =
            selectedAttribution?.vessel_id ===
            candidate.vessel_id;

          const isVOI =
            candidate.category ===
            'Vessel of Interest';

          // DEMO coordinates
          const offsetLat =
            idx === 0
              ? 0.008
              : idx === 1
                ? -0.015
                : idx === 2
                  ? 0.025
                  : -0.030;

          const offsetLon =
            idx === 0
              ? -0.012
              : idx === 1
                ? 0.020
                : idx === 2
                  ? 0.035
                  : -0.040;

          const vLat =
            activeIncident.latitude +
            offsetLat;

          const vLon =
            activeIncident.longitude +
            offsetLon;

          // -------------------------------------------------------
          // Vessel marker
          // -------------------------------------------------------

          const markerColor =
            isSelected
              ? '#ff3b30'
              : isVOI
                ? '#ff9f1c'
                : '#38d4e8';

          const customIcon = L.divIcon({
            className: 'vessel-map-icon',

            html: `
              <div style="
                width: ${isSelected ? 24 : 18}px;
                height: ${isSelected ? 24 : 18}px;
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
            `,

            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });

          const marker = L.marker(
            [vLat, vLon],
            {
              icon: customIcon
            }
          );

          marker.on(
            'click',
            () => {
              selectVessel(candidate);
            }
          );

          marker.bindPopup(`
            <div style="
              font-family: sans-serif;
              padding: 4px;
            ">
              <strong style="
                color: #e7f0f7;
                font-size: 13px;
              ">
                ${candidate.vessel_name}
              </strong>

              <br/>

              <span style="
                font-size: 11px;
                color: #9fb2c3;
              ">
                MMSI: ${candidate.mmsi}
              </span>

              <br/>

              <span style="
                font-size: 11px;
                color: ${markerColor};
                font-weight: bold;
              ">
                ${candidate.category}
                (${candidate.overall_score}%)
              </span>
            </div>
          `);

          layerGroup.addLayer(marker);

          // -------------------------------------------------------
          // Vessel trajectory
          // -------------------------------------------------------

          if (layers.vesselTrails) {

            const trailCoords:
              L.LatLngExpression[] = [
                [
                  vLat - 0.03,
                  vLon - 0.04
                ],
                [
                  vLat - 0.015,
                  vLon - 0.02
                ],
                [
                  vLat,
                  vLon
                ]
              ];

            const trailPolyline =
              L.polyline(
                trailCoords,
                {
                  color:
                    isSelected
                      ? '#ff3b30'
                      : '#27d17f',

                  weight:
                    isSelected
                      ? 3
                      : 2,

                  dashArray: '4, 4',
                  opacity: 0.8
                }
              );

            layerGroup.addLayer(
              trailPolyline
            );
          }
        }
      );
    }

    // -------------------------------------------------------------
    // 6. Render Real-Time AIS Vessels
    // -------------------------------------------------------------

    if (
      layers.vessels &&
      liveVessels.length > 0
    ) {

      liveVessels.forEach((lv) => {

        const isTarget =
          lv.is_target_of_interest;

        const color =
          isTarget
            ? '#ff3b30'
            : '#38d4e8';

        const liveIcon = L.divIcon({
          className: 'live-vessel-icon',

          html: `
            <div style="
              width: 14px;
              height: 14px;
              background: ${color};
              border: 2px solid #ffffff;
              border-radius: 50%;
              transform: rotate(${lv.heading_deg || 0}deg);
              box-shadow: 0 0 10px ${color};
            "></div>
          `,

          iconSize: [14, 14],
          iconAnchor: [7, 7]
        });

        const liveMarker = L.marker(
          [
            lv.latitude,
            lv.longitude
          ],
          {
            icon: liveIcon
          }
        );

        liveMarker.bindPopup(`
          <div style="
            font-family: monospace;
            padding: 6px;
            background: #040a12;
            color: #e7f0f7;
          ">

            <strong style="
              color: ${isTarget ? '#ff3b30' : '#32c7e8'};
              font-size: 13px;
            ">
              ${lv.name}
            </strong>

            <br/>

            <span style="
              font-size: 11px;
              color: #9fb2c3;
            ">
              IMO: ${lv.imo}
              |
              MMSI: ${lv.mmsi}
            </span>

            <br/>

            <span style="
              font-size: 11px;
              color: #9fb2c3;
            ">
              Type: ${lv.ship_type}
              (${lv.flag})
            </span>

            <br/>

            <span style="
              font-size: 11px;
              color: #36c879;
              font-weight: bold;
            ">
              KINEMATICS:
              ${lv.speed_knots} kts
              @ ${lv.heading_deg}° COG
            </span>

            <br/>

            <span style="
              font-size: 11px;
              color: #ff9f1c;
            ">
              Draft: ${lv.draft_m || 12.0}m
              |
              Dest: ${lv.destination || 'N/A'}
            </span>

            <br/>

            <span style="
              font-size: 10px;
              color: #6f8496;
            ">
              Receiver:
              ${lv.receiver_station}
              (${lv.signal_rssi_dbm} dBm)
            </span>

          </div>
        `);

        layerGroup.addLayer(
          liveMarker
        );
      });
    }

  }, [
    activeIncident,
    segmentation,
    oceanDrift,
    attributionScores,
    selectedAttribution,
    layers,
    liveVessels
  ]);

  // ---------------------------------------------------------------
  // Automatically zoom to REAL ML oil detection
  // ---------------------------------------------------------------

  useEffect(() => {

    const map = mapRef.current;

    if (
      !map ||
      !segmentation ||
      !segmentation.polygon_geojson ||
      !layers.spillPolygon
    ) {
      return;
    }

    try {

      const oilLayer = L.geoJSON(
        segmentation.polygon_geojson
      );

      const bounds = oilLayer.getBounds();

      if (bounds.isValid()) {

        map.fitBounds(
          bounds,
          {
            padding: [100, 100],
            maxZoom: 16,
            animate: true,
            duration: 1.2
          }
        );

      }

    } catch (error) {

      console.error(
        'Unable to zoom to ML oil detection:',
        error
      );

    }

  }, [
    segmentation,
    layers.spillPolygon
  ]);

  // ---------------------------------------------------------------
  // Map Legend
  // ---------------------------------------------------------------

  return (
    <div
      className="map-area"
      style={{
        width: '100%',
        height: '100%',
        position: 'relative'
      }}
    >

      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '100%'
        }}
      />

      {/* Map Legend Overlay */}

      <div
        style={{
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
          gap: '6px'
        }}
      >

        <div
          style={{
            fontWeight: 'bold',
            color: '#32c7e8',
            marginBottom: '2px'
          }}
        >
          MAP LEGEND
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <span
            style={{
              width: '12px',
              height: '12px',
              background: 'rgba(228, 61, 61, 0.4)',
              border: '1px solid #e43d3d',
              borderRadius: '3px'
            }}
          />

          <span>
            SAR Oil Slick Mask
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <span
            style={{
              width: '12px',
              height: '12px',
              background: 'rgba(50, 199, 232, 0.2)',
              border: '1px dashed #32c7e8',
              borderRadius: '3px'
            }}
          />

          <span>
            Probable Origin Zone
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <span
            style={{
              width: '12px',
              height: '3px',
              background: '#ff9f1c'
            }}
          />

          <span>
            24h Drift Forecast
          </span>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <span
            style={{
              width: '10px',
              height: '10px',
              background: '#ff3b30',
              borderRadius: '50%'
            }}
          />

          <span>
            Vessel of Interest
          </span>
        </div>

      </div>

    </div>
  );
};