import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
import asyncio
import json

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="OceanGuard - AI-Powered Maritime Oil Spill Detection & Vessel Attribution System API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - allow Vercel frontend
# In production set ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://oceanguard.onrender.com
origins = settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS != ["*"] else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "ONLINE",
        "docs": "/docs",
        "version": settings.VERSION
    }

# WebSocket for real-time AIS & incident updates (God's Eye smooth streaming)
@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        from app.services.ais_connector import get_live_ais_feed
        from app.services.gods_eye_adapter import SENSOR_STYLES
        step = 0
        while True:
            step += 1
            live = get_live_ais_feed()
            # Broadcast God's Eye compatible payload
            data = {
                "type": "VESSEL_TELEMETRY_UPDATE",
                "step": step,
                "timestamp": live.get("timestamp"),
                "source": live.get("source"),
                "sensor_style": "normal",
                "vessels": [
                    {
                        "mmsi": v["mmsi"],
                        "name": v["name"],
                        "lat": v["latitude"],
                        "lon": v["longitude"],
                        "speed_knots": v["speed_knots"],
                        "heading_deg": v["heading_deg"],
                        "course_deg": v.get("course_deg", v["heading_deg"]),
                        "trail": v.get("trail", []),
                        "world_stable_heading": v.get("world_stable_heading", v["heading_deg"]),
                        "threat_score": v.get("threat_score"),
                        "ship_type": v.get("ship_type"),
                        "flag": v.get("flag")
                    } for v in live.get("vessels", [])
                ],
                "provenance": live.get("provenance"),
                "hud": {
                    "sensor_styles": list(SENSOR_STYLES.keys()),
                    "detection_overlay": True
                }
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(2.5)  # God's Eye: 2.5s ticker matches frontend
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011, reason=str(e)[:100])
        except Exception:
            pass

@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": settings.VERSION}
