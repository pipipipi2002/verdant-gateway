from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Set
import asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Track active connections by type
        self.telemetry_connections: Dict[str, Set[WebSocket]] = {}
        self.video_connections: Dict[str, WebSocket] = {}
        
    async def connect_telemetry(self, websocket: WebSocket, device_id: str):
        """Connect client for telemetry updates"""
        await websocket.accept()
        
        if device_id not in self.telemetry_connections:
            self.telemetry_connections[device_id] = set()
        
        self.telemetry_connections[device_id].add(websocket)
        logger.info(f"Telemetry WebSocket connected for device {device_id}")
        
    async def connect_video(self, websocket: WebSocket, device_id: str):
        """Connect client for video streaming"""
        await websocket.accept()
        
        # Only one video connection per device
        if device_id in self.video_connections:
            await self.video_connections[device_id].close()
        
        self.video_connections[device_id] = websocket
        logger.info(f"Video WebSocket connected for device {device_id}")
        
    def disconnect_telemetry(self, websocket: WebSocket, device_id: str):
        """Remove telemetry connection"""
        if device_id in self.telemetry_connections:
            self.telemetry_connections[device_id].discard(websocket)
            
            if not self.telemetry_connections[device_id]:
                del self.telemetry_connections[device_id]
                
    def disconnect_video(self, device_id: str):
        """Remove video connection"""
        if device_id in self.video_connections:
            del self.video_connections[device_id]
            
    async def broadcast_telemetry(self, device_id: str, data: dict):
        """Broadcast telemetry to all connected clients"""
        if device_id not in self.telemetry_connections:
            return
            
        dead_connections = set()
        
        for websocket in self.telemetry_connections[device_id]:
            try:
                await websocket.send_json(data)
            except Exception:
                dead_connections.add(websocket)
                
        # Clean up dead connections
        for websocket in dead_connections:
            self.disconnect_telemetry(websocket, device_id)
            
    async def relay_video_frame(self, device_id: str, frame_data: bytes):
        """Relay video frame to connected client"""
        if device_id in self.video_connections:
            try:
                await self.video_connections[device_id].send_bytes(frame_data)
            except Exception:
                self.disconnect_video(device_id)


# WebSocket endpoints
@router.websocket("/telemetry/{device_id}")
async def websocket_telemetry(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for real-time telemetry"""
    from app.main import websocket_manager, mqtt_bridge
    
    # Verify device exists
    from app.services.data_store import data_store
    if device_id not in data_store.devices:
        await websocket.close(code=1008, reason="Device not found")
        return
        
    await websocket_manager.connect_telemetry(websocket, device_id)
    
    try:
        # Subscribe to MQTT telemetry updates
        async def on_telemetry(topic: str, payload: dict):
            if payload.get("device_id") == device_id:
                await websocket_manager.broadcast_telemetry(device_id, payload)
                
        await mqtt_bridge.subscribe(f"devices/{device_id}/telemetry", on_telemetry)
        
        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong)
            message = await websocket.receive_text()
            
            if message == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        websocket_manager.disconnect_telemetry(websocket, device_id)
        logger.info(f"Telemetry WebSocket disconnected for device {device_id}")

@router.websocket("/video/{device_id}")
async def websocket_video(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for video streaming relay"""
    from app.main import websocket_manager, mqtt_bridge
    
    # Verify device exists
    from app.services.data_store import data_store
    if device_id not in data_store.devices:
        await websocket.close(code=1008, reason="Device not found")
        return
        
    await websocket_manager.connect_video(websocket, device_id)
    
    try:
        # TODO: Subscribe to video stream from device
        # For now, simulate video frames
        frame_count = 0
        
        while True:
            # Check if websocket is still connected
            try: 

                # In production, this would relay actual video frames from the device
                # For simulation, send a frame counter
                
                frame_data = {
                    "type": "frame",
                    "device_id": device_id,
                    "frame": frame_count,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send_json(frame_data)
                
                frame_count += 1
                await asyncio.sleep(0.033)  # ~30 FPS
            except Exception as e:
                logger.error(f"Error sending video frame: {e}")
                break
            
    except WebSocketDisconnect:
        logger.info(f"Video WebSocket disconnected for device {device_id}")
    except Exception as e:
        logger.error(f"Video WebSocket error: {e}")
    finally:
        websocket_manager.disconnect_video(device_id)
