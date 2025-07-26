from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
from typing import Dict, List
import uvicorn
import sys
import os
import logging 

# Add the parent directory to the path to handle different running scenarios
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logger = logging.getLogger(__name__)


from app.api.v1 import farms, devices, telemetry, websocket
# from app.services.mqtt_bridge import MQTTBridge
from app.services.mqtt_client import mqtt_client
from app.services.device_manager import DeviceManager
from app.utils.monitoring import GatewayMonitor
from app.config import settings

# Global instances
# mqtt_bridge = None
device_manager = None
gateway_monitor = None
websocket_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # global mqtt_bridge, device_manager, gateway_monitor, websocket_manager
    global device_manager, gateway_monitor, websocket_manager
    
    # Initilize database connection
    from app.services.database import db_service
    await db_service.connect()

    # Initialize services
    # mqtt_bridge = MQTTBridge()
    device_manager = DeviceManager()
    gateway_monitor = GatewayMonitor()
    websocket_manager = websocket.WebSocketManager()

    # Start MQTT client
    try:
        await mqtt_client.start()
        
    except Exception as e:
        logger.error(f"Failed to start MQTT client: {e}")
        logger.warning("Continuing without MQTT connection")
    
    # Start background services
    # asyncio.create_task(mqtt_bridge.start())
    asyncio.create_task(gateway_monitor.start_monitoring())
    
    # Set up dummy data
    await device_manager.initialize_dummy_data()
    
    yield
    
    # Shutdown
    # await mqtt_bridge.stop()
    await mqtt_client.stop()
    await gateway_monitor.stop_monitoring()
    await db_service.disconnect()

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
    from app.utils.logging_config import setup_logging
    from app.config import settings
    setup_logging(settings.log_level)
    
    # When running directly, use the current module
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)