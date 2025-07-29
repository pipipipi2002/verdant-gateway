from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class Device(BaseModel):
    id: str
    farm_id: str
    name: str
    plant_name: str
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_seen: datetime
    snapshot_url: Optional[str] = None
    telemetry_interval: int = 60  # seconds
    snapshot_interval: int = 3600  # seconds
    location: Optional[str] = None
    firmware_version: str = "1.0.0"
    ip_address: Optional[str] = None
    
class DeviceStatusData(BaseModel):
    device_id: str
    timestamp: datetime
    status: DeviceStatus  
    firmware_version: str
    uptime_seconds: int
    rssi: int  # WiFi signal strength
    error_code: int
    error_message: str
    free_memory: Optional[int] = None  # Bytes
    internal_temperature: float  # Device internal temperature
    internal_humidity: float  # Device internal humidity
    battery_level: Optional[int] = None  # Percentage (0-100)

class DeviceDetail(Device):
    current_telemetry: Dict[str, Any]
    current_status: Optional[DeviceStatusData] = None
    commands_available: List[str]
    total_telemetry_today: int