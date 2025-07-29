from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
import base64
from datetime import datetime, timezone

from app.models.device import Device, DeviceDetail, DeviceStatus
from app.models.telemetry import TelemetryUpdate, DeviceCommand
from app.services.database import db_service
from app.services.data_store import data_store

router = APIRouter()

@router.get("/", response_model=List[Device])
async def get_devices(farm_id: Optional[str] = None, status: Optional[DeviceStatus] = None):
    """Get all devices, optionally filtered"""
    devices = await db_service.get_devices(farm_id)
    
    if status:
        devices = [d for d in devices if d.status == status]
    
    return devices

@router.get("/{device_id}", response_model=DeviceDetail)
async def get_device(device_id: str):
    """Get device details"""
    device = await db_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get device status from MQTT cache
    from app.services.mqtt_client import mqtt_client
    status_info = mqtt_client.device_status_cache.get(device_id, {})

    # TODO: What is the point of getting from cache + database when we can just take all from cache?
    # Update device status if available in cache
    if status_info:
        device.status = DeviceStatus(status_info.get("status", "offline"))

    # Get latest device status from database for history
    device_status = await db_service.get_latest_device_status(device_id)

    # Get latest telemetry
    latest_telemetry = await data_store.get_latest_telemetry(device_id)
    current_telemetry = {}
    
    if latest_telemetry:
        current_telemetry = {
            "env_temperature": f"{latest_telemetry.env_temperature:.1f}°C",
            "humidity": f"{latest_telemetry.humidity:.1f}%",
            "pressure": f"{latest_telemetry.pressure:.1f} hPa",
            "light": f"{latest_telemetry.light:.0f} lux",
            "co2": f"{latest_telemetry.co2:.0f} ppm",
            "voc": f"{latest_telemetry.voc:.0f} ppb",
            "soil_temperature": f"{latest_telemetry.soil_temperature:.1f}°C",
            "soil_moisture": f"{latest_telemetry.soil_moisture:.1f}%",
            "soil_ph": f"{latest_telemetry.soil_ph:.2f}"
        }
    
    # Count telemetry entries
    telemetry_history = await data_store.get_telemetry_history(device_id, 24)
    telemetry_count = len(telemetry_history)
    
    return DeviceDetail(
        **device.model_dump(),
        current_telemetry=current_telemetry,
        current_status=device_status,
        commands_available=["restart", "update_config", "capture_snapshot", "start_stream"],
        total_telemetry_today=telemetry_count
    )

@router.patch("/{device_id}/config")
async def update_device_config(device_id: str, config: TelemetryUpdate):
    """Update device telemetry intervals"""
    from app.main import device_manager
    
    device = await db_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    config_dict = config.model_dump(exclude_unset=True)
    success = await device_manager.update_device_config(device_id, config_dict)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update configuration")
    
    return {"status": "success", "updated": config_dict}

@router.post("/{device_id}/command")
async def send_device_command(device_id: str, command: DeviceCommand):
    """Send command to device"""
    from app.main import device_manager
    
    device = await db_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    success = await device_manager.send_command(device_id, command)
    
    return {"status": "queued" if success else "failed", "command": command.command}

@router.get("/{device_id}/snapshot")
async def get_device_snapshot(device_id: str):
    """Get latest snapshot. TODO: Retrieve from storage"""
    # For now, return a placeholder image
    placeholder = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    
    return {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), 
        "image": f"data:image/png;base64,{placeholder}"
    }

@router.post("/{device_id}/snapshot")
async def upload_snapshot(device_id: str, file: UploadFile = File(...)):
    """Upload new snapshot. TODO: Store in filesystem/S3"""
    if device_id not in data_store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # TODO: Store file properly
    # For now, just acknowledge
    return {
        "status": "success",
        "device_id": device_id,
        "filename": file.filename,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }