from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class TelemetryData(BaseModel):
    device_id: str
    timestamp: datetime
    env_temperature: float      # Environmental temperature (celsius)
    humidity: float             # Environmental humidity (percentage)
    pressure: float             # Atmospheric pressure (hPa)
    light: float                # Light intensity (lux)
    co2: float                  # CO2 concentration (ppm)
    voc: float                  # Volatile Organic Compounds (ppb)
    soil_temperature: float     # Soil temperature (celsius)
    soil_moisture: float        # Soil moisture (percentage)
    soil_ph: float              # Soil pH value
    
class TelemetryUpdate(BaseModel):
    telemetry_interval: Optional[int] = None
    snapshot_interval: Optional[int] = None
    
class DeviceCommand(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}