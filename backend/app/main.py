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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# WebSocket for real-time AIS & incident updates
@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        step = 0
        while True:
            # Broadcast mock live vessel position updates
            step += 1
            data = {
                "type": "VESSEL_TELEMETRY_UPDATE",
                "step": step,
                "vessels": [
                    {
                        "mmsi": 636018432,
                        "name": "PACIFIC EXPLORER",
                        "lat": round(1.3120 + (step * 0.0002), 5),
                        "lon": round(103.8540 + (step * 0.0003), 5),
                        "speed_knots": 5.4,
                        "heading_deg": 68.0
                    },
                    {
                        "mmsi": 352001928,
                        "name": "OCEAN GEMINI",
                        "lat": round(1.2400 + (step * 0.0005), 5),
                        "lon": round(103.7900 + (step * 0.0006), 5),
                        "speed_knots": 12.8,
                        "heading_deg": 72.0
                    }
                ]
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(4.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
