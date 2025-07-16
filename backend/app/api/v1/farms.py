from fastapi import APIRouter, HTTPException
from typing import List

from app.models.farm import Farm, FarmDetail
from app.services.data_store import data_store
from app.utils.monitoring import GatewayMonitor

router = APIRouter()

@router.get("/", response_model=List[Farm])
async def get_farms():
    """Get all farms"""
    return list(data_store.farms.values())

@router.get("/{farm_id}", response_model=FarmDetail)
async def get_farm(farm_id: str):
    """Get farm details"""
    if farm_id not in data_store.farms:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    farm = data_store.farms[farm_id]
    
    # Get gateway metrics
    from app.main import gateway_monitor
    metrics = await gateway_monitor.get_metrics()
    
    # Count telemetry entries today
    total_telemetry = sum(len(entries) for entries in data_store.telemetry.values())
    
    return FarmDetail(
        **farm.model_dump(),
        gateway_hardware={
            "model": "RaspberryPi 4B",
            "cpu": "ARM Cortex-A72",
            "memory": "4GB",
            "storage": "32GB"
        },
        resource_utilization={
            "cpu": metrics["cpu_percent"],
            "memory": metrics["memory_percent"],
            "disk": metrics["disk_percent"]
        },
        total_telemetry_today=total_telemetry
    )