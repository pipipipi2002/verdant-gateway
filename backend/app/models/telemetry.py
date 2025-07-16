from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class TelemetryData(BaseModel):
    device_id: str
    timestamp: datetime
    soil_humidity: float  # percentage
    soil_temperature: float  # celsius
    co2: float  # ppm
    device_temperature: float  # celsius
    device_humidity: float  # percentage
    status: str

class TelemetryInternalData(BaseModel):
    device_id: str
    timestamp: datetime
    temperature: float  # celsius
    humidity: float  # percentage
    batt: float # voltage
    status: str

class TelemetryEnvironmentData(BaseModel):
    device_id: str
    timestamp: datetime
    temperature: float
    humidity: float
    pressure: float
    light: float
    co2: float
    voc: float
    status: str

class TelemetrySoilData(BaseModel):
    device_id: str
    timestamp: datetime
    temperature: float
    moisture: float
    ph: float
    status: str
    
class TelemetryUpdate(BaseModel):
    telemetry_interval: Optional[int] = None
    snapshot_interval: Optional[int] = None
    
class DeviceCommand(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}