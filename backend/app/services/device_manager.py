import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

from app.models.device import Device, DeviceStatus
from app.models.telemetry import DeviceCommand
from app.services.data_store import data_store
from app.services.database import db_service
from app.services.mqtt_client import mqtt_client

logger = logging.getLogger(__name__)

class DeviceManager:
    """Manages device lifecycle and commands"""
    
    def __init__(self):
        self.command_queue: Dict[str, List[DeviceCommand]] = {}
        self.device_tasks: Dict[str, asyncio.Task] = {}
        
    async def initialize_dummy_data(self):
        """Initialize dummy data in the data store"""
        await data_store.initialize_dummy_data()
    
    async def send_command(self, device_id: str, command: DeviceCommand) -> bool:
        """Queue command for device. TODO: Send via MQTT"""
        if device_id not in self.command_queue:
            self.command_queue[device_id] = []
        
        self.command_queue[device_id].append(command)
        
        # TODO: Publish to MQTT topic devices/{device_id}/commands
        await mqtt_client.publish(
            f"devices/{device_id}/commands",
            {
                "command": command.command,
                "parameters": command.parameters,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        return True
    
    async def update_device_config(self, device_id: str, config: Dict) -> bool:
        """Update device configuration"""
        device = await db_service.get_device(device_id)
        if not device:
            return False
        
        #TODO: Update in db
        await mqtt_client.publish(
            f"devices/{device_id}/config",
            {
                **config,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            retain=True
        )
        
        return True
    
    async def register_device(self, device: Device) -> bool:
        """Register new device. TODO: Implement provisioning"""
        try:
            async with db_service.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO devices (id, farm_id, name, plant_name, status, last_seen, 
                                    telemetry_interval, snapshot_interval, location, firmware_version)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''', device.id, device.farm_id, device.name, device.plant_name, 
                    device.status.value, device.last_seen, device.telemetry_interval,
                    device.snapshot_interval, device.location, device.firmware_version)
            
            return True
        except Exception as e:
            logger.error(f"Error registering device: {e}")
            return False