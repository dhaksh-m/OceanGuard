import { 
  Incident, 
  SegmentationResult, 
  OceanDriftResult, 
  Vessel, 
  AttributionScore, 
  EvidenceItem 
} from '../types';

const API_BASE = '/api/v1';

export async function fetchIncidents(): Promise<Incident[]> {
  const res = await fetch(`${API_BASE}/incidents`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchIncidentById(id: string): Promise<Incident> {
  const res = await fetch(`${API_BASE}/incidents/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch incident ${id}`);
  return res.json();
}

export async function createIncident(data: { name: string; region: string; latitude: number; longitude: number }): Promise<Incident> {
  const res = await fetch(`${API_BASE}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create incident');
  return res.json();
}

export async function fetchSegmentation(incidentId: string): Promise<SegmentationResult> {
  const res = await fetch(`${API_BASE}/segmentation/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId })
  });
  if (!res.ok) throw new Error('Failed to run segmentation prediction');
  return res.json();
}

export async function fetchOceanDrift(incidentId: string, lat: number, lon: number): Promise<OceanDriftResult> {
  const res = await fetch(`${API_BASE}/ocean/drift?incident_id=${incidentId}&lat=${lat}&lon=${lon}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to calculate ocean drift simulation');
  return res.json();
}

export async function fetchVessels(): Promise<Vessel[]> {
  const res = await fetch(`${API_BASE}/ais/vessels`);
  if (!res.ok) throw new Error('Failed to fetch AIS vessels');
  return res.json();
}

export async function fetchLiveVessels(): Promise<any> {
  const res = await fetch(`${API_BASE}/ais/live`);
  if (!res.ok) throw new Error('Failed to fetch live AIS stream positions');
  return res.json();
}

export async function fetchAttribution(incidentId: string): Promise<AttributionScore[]> {
  const res = await fetch(`${API_BASE}/attribution/calculate?incident_id=${incidentId}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to calculate vessel attribution scores');
  return res.json();
}

export async function fetchEvidence(incidentId: string): Promise<EvidenceItem[]> {
  const res = await fetch(`${API_BASE}/evidence/${incidentId}`);
  if (!res.ok) throw new Error('Failed to fetch evidence locker items');
  return res.json();
}

export async function triggerSceneIngest(sceneId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/satellite/scenes/ingest?scene_id=${sceneId}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to ingest scene');
  return res.json();
}
