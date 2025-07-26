from pydantic_settings import BaseSettings
from typing import Dict

class Settings(BaseSettings):
    # Server config
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging Config
    log_level: str = "INFO"

    # Database config
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "plant_monitoring"

    # MQTT config
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_user: str = "admin"
    mqtt_pass: str = "admin"
    mqtt_topics: Dict[str, str] = {
        "telemetry_internal": "devices/+/telemetry/int",
        "telemetry_env": "devices/+/telemetry/env",
        "telemetry_soil": "devices/+/telemetry/soil",
        "status": "devices/+/status",
        "snapshot": "devices/+/snapshot",
        "video_metadata": "devices/+/video/metadata",
        "alerts": "devices/+/alerts"
    }

    # Gateway config
    gateway_id: str = "gateway-001"
    farm_id: str = "farm-001"

    # Data retention
    telemetry_buffer_size: int = 1000
    snapshot_retention_hours: int = 24

settings = Settings()