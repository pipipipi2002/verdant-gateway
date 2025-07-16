import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from app.models.device import Device, DeviceStatus
from app.models.telemetry import DeviceCommand
from app.services.data_store import data_store

class DeviceManager:
    """Manages device lifecycle and commands"""
    
    def __init__(self):
        self.command_queue: Dict[str, List[DeviceCommand]] = {}
        self.device_tasks: Dict[str, asyncio.Task] = {}
        
    async def initialize_dummy_data(self):
        """Initialize dummy data in the data store"""
        await data_store.initialize_dummy_data()
        
        # Start device simulation tasks
        for device_id, device in data_store.devices.items():
            if device.status == DeviceStatus.ONLINE:
                self.device_tasks[device_id] = asyncio.create_task(
                    self._simulate_device(device_id)
                )
    
    async def _simulate_device(self, device_id: str):
        """Simulate device telemetry. TODO: Remove when real devices connect"""
        import random
        from app.models.telemetry import TelemetryData
        
        while True:
            device = data_store.devices.get(device_id)
            if not device or device.status != DeviceStatus.ONLINE:
                break
                
            # Generate telemetry
            telemetry = TelemetryData(
                device_id=device_id,
                timestamp=datetime.now(),
                soil_humidity=random.uniform(40, 80),
                soil_temperature=random.uniform(20, 30),
                co2=random.uniform(350, 450),
                device_temperature=random.uniform(25, 35),
                device_humidity=random.uniform(50, 70),
                status="normal"
            )
            
            await data_store.add_telemetry(telemetry)
            
            # TODO: Publish to MQTT for WebSocket relay
            
            await asyncio.sleep(device.telemetry_interval)
    
    async def send_command(self, device_id: str, command: DeviceCommand) -> bool:
        """Queue command for device. TODO: Send via MQTT"""
        if device_id not in self.command_queue:
            self.command_queue[device_id] = []
        
        self.command_queue[device_id].append(command)
        
        # TODO: Publish to MQTT topic devices/{device_id}/commands
        
        return True
    
    async def update_device_config(self, device_id: str, config: Dict) -> bool:
        """Update device configuration"""
        if device_id in data_store.devices:
            device = data_store.devices[device_id]
            
            if "telemetry_interval" in config:
                device.telemetry_interval = config["telemetry_interval"]
            if "snapshot_interval" in config:
                device.snapshot_interval = config["snapshot_interval"]
                
            # TODO: Send config update via MQTT
            
            return True
        return False
    
    async def register_device(self, device: Device) -> bool:
        """Register new device. TODO: Implement provisioning"""
        data_store.devices[device.id] = device
        return True