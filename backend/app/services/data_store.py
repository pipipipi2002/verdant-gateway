from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, deque
import random

from app.models.farm import Farm, ConnectionStatus
from app.models.device import Device, DeviceStatus
from app.models.telemetry import TelemetrySoilData, TelemetryInternalData, TelemetryEnvironmentData, TelemetryData

class DataStore:
    """Temporary in-memory data store. TODO: Replace with TimescaleDB"""

    def __init__(self):
        self.farms: Dict[str, Farm] = {}
        self.devices: Dict[str, Device] = {}
        self.telemetry: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.snapshot: Dict[str, str] = {}

    async def initialize_dummy_data(self):
        """Create dummy data for testing"""
        # Create farm
        farm = Farm(
            id="farm-001",
            name="Xuen Toilet",
            location="E8 NUS, Singapore",
            device_count=5,
            active_devices=4,
            offline_devices=1,
            connection_status=ConnectionStatus.LOCAL,
            gateway_id="gateway-001",
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now()
        )
        self.farms[farm.id] = farm

        # Create devices
        plant_names = ["Tomato A1", "Lettuce B2", "Basil C3", "Pepper D4", "Spinach E5"]
        for i in range(5):
            device = Device(
                id=f"device-{i+1:03d}",
                farm_id="farm-001",
                name=f"Sensor Unit {i+1}",
                plant_name=plant_names[i],
                status=DeviceStatus.OFFLINE if i == 4 else DeviceStatus.ONLINE,
                last_seen=datetime.now() - timedelta(minutes=5 if i != 4 else 120),
                snapshot_url=f"/api/v1/devices/device-{i+1:03d}/snapshot",
                telemetry_interval=60,
                snapshot_interval=3600,
                location=f"Row {i//2 + 1}, Position {i%2 + 1}",
                firmware_version="1.0.0"
            )
            self.devices[device.id] = device
            
            # Generate historical telemetry
            if device.status == DeviceStatus.ONLINE:
                await self._generate_telemetry_history(device.id)

    async def _generate_telemetry_history(self, device_id: str):
        """Generate dummy telemetry history"""
        now = datetime.now()
        for hours_ago in range(24, 0, -1):
            telemetry = TelemetryData(
                device_id=device_id,
                timestamp=now - timedelta(hours=hours_ago),
                soil_humidity=random.uniform(40, 80),
                soil_temperature=random.uniform(20, 30),
                co2=random.uniform(350, 450),
                device_temperature=random.uniform(25, 35),
                device_humidity=random.uniform(50, 70),
                status="normal"
            )
            self.telemetry[device_id].append(telemetry)
    
    async def get_latest_telemetry(self, device_id: str) -> Optional[TelemetryData]:
        """Get latest telemetry for a device"""
        if device_id in self.telemetry and self.telemetry[device_id]:
            return self.telemetry[device_id][-1]
        return None
    
    async def add_telemetry(self, telemetry: TelemetryData):
        """Add new telemetry data. TODO: Store in TimescaleDB"""
        self.telemetry[telemetry.device_id].append(telemetry)
        
        # Update device last_seen
        if telemetry.device_id in self.devices:
            self.devices[telemetry.device_id].last_seen = telemetry.timestamp
            self.devices[telemetry.device_id].status = DeviceStatus.ONLINE
    
    async def get_telemetry_history(self, device_id: str, hours: int = 24) -> List[TelemetryData]:
        """Get telemetry history. TODO: Query from TimescaleDB"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [t for t in self.telemetry[device_id] if t.timestamp > cutoff]
    

data_store = DataStore()