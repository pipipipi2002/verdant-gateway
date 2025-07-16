from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.models.telemetry import TelemetryData
from app.services.data_store import data_store

router = APIRouter()

@router.get("/{device_id}", response_model=List[TelemetryData])
async def get_device_telemetry(
    device_id: str,
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve")
):
    """Get telemetry history for a device"""
    if device_id not in data_store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    telemetry = await data_store.get_telemetry_history(device_id, hours)
    
    if not telemetry:
        return []
    
    return telemetry

@router.post("/{device_id}")
async def add_telemetry(device_id: str, telemetry: TelemetryData):
    """Add telemetry data. Usually called by MQTT bridge"""
    if device_id not in data_store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Validate device_id matches
    if telemetry.device_id != device_id:
        raise HTTPException(status_code=400, detail="Device ID mismatch")
    
    await data_store.add_telemetry(telemetry)
    
    # TODO: Notify WebSocket subscribers
    
    return {"status": "success", "timestamp": telemetry.timestamp}

@router.get("/{device_id}/latest", response_model=Optional[TelemetryData])
async def get_latest_telemetry(device_id: str):
    """Get most recent telemetry for a device"""
    if device_id not in data_store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return await data_store.get_latest_telemetry(device_id)
