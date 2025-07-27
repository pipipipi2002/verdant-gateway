from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState
from typing import Dict, Set
import asyncio
import json
import logging
from datetime import datetime, timezone

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

    async def broadcast_status(self, device_id: str, data: dict):
        """Broadcast device status to all telemetry subscribers"""
        # Status updates go to telemetry subscribers too
        await self.broadcast_telemetry(device_id, {
            "type": "status",
            "device_id": device_id,
            "data": data
        })
            
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
    from app.main import websocket_manager
    from app.services.database import db_service
    
    # Verify device exists
    device = await db_service.get_device(device_id)
    
    if not device:
        await websocket.close(code=1008, reason="Device not found")
        return
        
    await websocket_manager.connect_telemetry(websocket, device_id)
    
    try:
        # Keep connection alive
        while True:
            try:
                # Wait for client messages (ping/pong)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                if message == "ping":
                    await websocket.send_text("pong")
                
            except asyncio.TimeoutError:
                # Send ping to check if client is still alive
                try: 
                    await websocket.send_text("ping")
                except Exception:
                    break
                
    except WebSocketDisconnect:
        logger.info(f"Telemetry WebSocket disconnected for device {device_id}")
    except Exception as e:
        logger.error(f"Telemetry WebsSocket Error: {e}")
    finally:
        websocket_manager.disconnect_telemetry(websocket, device_id)

@router.websocket("/video/{device_id}")
async def websocket_video(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for video streaming relay"""
    from app.main import websocket_manager
    from app.services.database import db_service
    
    # Verify device exists
    device = await db_service.get_device(device_id)
    if not device:
        await websocket.close(code=1008, reason="Device not found")
        return
        
    await websocket_manager.connect_video(websocket, device_id)
    
    # TODO: Notify device to start sending video
    logger.info(f"Starting video stream for device {device_id}")
    try:
        from app.services.mqtt_client import mqtt_client
        logger.info(f"Seding MQTT message to start stream")
        await mqtt_client.publish(
            f"devices/{device_id}/commands",
            {
                "command": "start_stream",
                "parameters": {"quality": "high", "fps": 30}
            }
        )
    except Exception as e:
        logger.error(f"Failed to notify device to start streaming: {e}")

    try:
        # TODO: Subscribe to video stream from device
        # For now, simulate video frames
        frame_count = 0
        
        while True:
            # Check if websocket is still connected
            try: 
                # Check connection status
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.info(f"Client disconnected from video stream for device {device_id}")
                    break

                # In production, this would relay actual video frames from the device
                # For simulation, send a frame counter
                
                frame_data = {
                    "type": "frame",
                    "device_id": device_id,
                    "frame": frame_count,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await websocket.send_json(frame_data)
                
                frame_count += 1
                await asyncio.sleep(0.033)  # ~30 FPS
            
            except WebSocketDisconnect:
                logger.info(f"Client closed video stream for device {device_id}")
                break
            except RuntimeError as e:
                # Handle runtime errors like "Cannot call send() on a closed WebSocket"
                if "closed" in str(e).lower():
                    logger.info(f"Video stream connection closed for device {device_id}")
                else:
                    logger.error(f"Runtime error in video stream: {e}")
                break
            except Exception as e:
                # Check if it's a connection closed error by examining the error message
                error_msg = str(e).lower()
                if any(word in error_msg for word in ["close", "disconnect", "broken"]):
                    logger.info(f"Video stream ended for device {device_id}")
                elif type(e).__name__ == "ClientDisconnected":
                    logger.info(f"Video stream ended for device {device_id}")
                else:
                    logger.error(f"Error sending video frame: {type(e).__name__}: {e}")
                break
            
    except WebSocketDisconnect:
        logger.info(f"Video WebSocket disconnected for device {device_id}")
    except Exception as e:
        logger.error(f"Video WebSocket error: {e}")
    finally:
        # Clean up shutdown procedures
        logger.info(f"Cleaning up video stream for device {device_id}")

        # Disconnect from manager
        websocket_manager.disconnect_video(device_id)

        # Notify device to stop streaming
        try:
            from app.services.mqtt_client import mqtt_client
            logger.info(f"Seding MQTT message to stop stream")

            await mqtt_client.publish(
                f"devices/{device_id}/commands",
                {
                    "command": "stop_stream",
                    "parameters": {}
                }
            )
            logger.info(f"Notified device {device_id} to stop streaming")

        except Exception as e:
            logger.error(f"Failed to notify device to stop streaming: {e}")
        
