from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceStatusData(BaseModel):
    device_id: str
    timestamp: datetime
    status: str  # online|offline|error|maintenance
    firmware_version: str
    ip_address: str
    uptime_seconds: int
    rssi: int  # WiFi signal strength
    error_code: int
    error_message: str
    free_memory: Optional[int] = None  # Bytes
    internal_temperature: float  # Device internal temperature
    internal_humidity: float  # Device internal humidity
    battery_level: Optional[int] = None  # Percentage (0-100)