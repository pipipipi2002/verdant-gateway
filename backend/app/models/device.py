from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

class Device(BaseModel):
    id: str
    farm_id: str
    name: str
    plant_name: str
    status: DeviceStatus
    last_seen: datetime
    snapshot_url: Optional[str] = None
    telemetry_interval: int = 60  # seconds
    snapshot_interval: int = 3600  # seconds
    location: Optional[str] = None
    firmware_version: str = "1.0.0"
    
class DeviceDetail(Device):
    current_telemetry: Dict[str, Any]
    commands_available: List[str]
    uptime_hours: float
    total_telemetry_today: int
