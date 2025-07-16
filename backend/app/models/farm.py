from pydantic import BaseModel
from typing import Dict
from datetime import datetime
from enum import Enum

class ConnectionStatus(str, Enum):
    LOCAL = "local"
    REMOTE = "remote"
    OFFLINE = "offline"

class Farm(BaseModel):
    id: str
    name: str
    location: str
    device_count: int
    active_devices: int
    offline_devices: int
    connection_status: ConnectionStatus
    gateway_id: str
    created_at: datetime
    updated_at: datetime

class FarmDetail(Farm):
    gateway_hardware: Dict[str, str]
    resource_utilization: Dict[str, float]
    total_telemetry_today: int