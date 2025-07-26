from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, deque
import random
import logging

from app.models.farm import Farm, ConnectionStatus
from app.models.device import Device, DeviceStatus
from app.models.telemetry import TelemetrySoilData, TelemetryInternalData, TelemetryEnvironmentData, TelemetryData
from app.services.database import db_service

logger = logging.getLogger(__name__)

class DataStore:
    """Temporary in-memory data store. TODO: Replace with TimescaleDB"""

    def __init__(self):
        # In-memory cache for fast access
        self.telemetry_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.snapshots: Dict[str, str] = {}

    async def initialize_dummy_data(self):
        try:
            await db_service.populate_dummy_data()
        except Exception as e:
            logger.error(f"Failed to initialise dummy data: {e}")
    
    async def get_latest_telemetry(self, device_id: str) -> Optional[TelemetryData]:
        # Get latest telemetry for a device
        if device_id in self.telemetry_cache and self.telemetry_cache[device_id]:
            return self.telemetry_cache[device_id][-1]
        
        # Fallback to database
        return await db_service.get_latest_telemetry(device_id)
    
    async def add_telemetry(self, telemetry: TelemetryData):
        """Add new telemetry data"""
        # Add to cache
        self.telemetry_cache[telemetry.device_id].append(telemetry)
        
        # Store in database
        await db_service.add_telemetry(telemetry)

        logger.debug(f"Added telemetry for device {telemetry.device_id}")
    
    async def get_telemetry_history(self, device_id: str, hours: int = 24) -> List[TelemetryData]:
        """Get telemetry history"""
        return await db_service.get_telemetry_history(device_id, hours)
    
    # Properties to maintain compatibility with existing code
    @property
    async def farms(self) -> Dict[str, Farm]:
        """Get all farms as a dict for compatibility"""
        farms_list = await db_service.get_farms()
        return {farm.id: farm for farm in farms_list}
    
    @property
    async def devices(self) -> Dict[str, Device]:
        """Get all devices as a dict for compatibility"""
        devices_list = await db_service.get_devices()
        return {device.id: device for device in devices_list}
    

data_store = DataStore()