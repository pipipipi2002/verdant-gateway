from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, List
import uvicorn
import sys
import os

# Add the parent directory to the path to handle different running scenarios
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.v1 import farms, devices, telemetry, websocket
from app.services.mqtt_bridge import MQTTBridge
from app.services.device_manager import DeviceManager
from app.utils.monitoring import GatewayMonitor
from app.config import settings

# Global instances
mqtt_bridge = None
device_manager = None
gateway_monitor = None
websocket_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mqtt_bridge, device_manager, gateway_monitor, websocket_manager
    
    # Initialize services
    mqtt_bridge = MQTTBridge()
    device_manager = DeviceManager()
    gateway_monitor = GatewayMonitor()
    websocket_manager = websocket.WebSocketManager()
    
    # Start background services
    asyncio.create_task(mqtt_bridge.start())
    asyncio.create_task(gateway_monitor.start_monitoring())
    
    # Set up dummy data
    await device_manager.initialize_dummy_data()
    
    yield
    
    # Shutdown
    await mqtt_bridge.stop()
    await gateway_monitor.stop_monitoring()

app = FastAPI(
    title="Plant Monitoring Gateway",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(farms.router, prefix="/api/v1/farms", tags=["farms"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["telemetry"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["websocket"])

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "gateway": await gateway_monitor.get_metrics()
    }

# Serve frontend (in production)
# app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

if __name__ == "__main__":
    # When running directly, use the current module
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)