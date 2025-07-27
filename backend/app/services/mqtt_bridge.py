import asyncio
import json
from typing import Callable, Dict, List
from datetime import datetime, timezone
import logging

from app.models.telemetry import TelemetryData
from app.services.data_store import data_store

logger = logging.getLogger(__name__)

class MQTTBridge:
    """Bridge between MQTT and HTTP/WebSocket. TODO: Implement actual MQTT client"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.connected = False
        self._telemetry_task = None
        
    async def start(self):
        """Start MQTT connection. TODO: Connect to actual MQTT broker"""
        logger.info("Starting MQTT bridge (simulation)")
        self.connected = True

        # Subscribe to all device telemetry topics
        await self.subscribe("devices/+/telemetry", self._handle_telemetry)
        await self.subscribe("devices/+/status", self._handle_status)

        # Simulate incoming messages
        self._telemetry_task = asyncio.create_task(self._simulate_mqtt_messages())

        logger.info("MQTT bridge started and subscribed to all device topics")
    
    async def stop(self):
        """Stop MQTT connection"""
        self.connected = False

        if self._telemetry_task:
            self._telemetry_task.cancel()
            try:
                await self._telemetry_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped MQTT bridge")

    async def _handle_telemetry(self, topic: str, payload: Dict):
        try:
            # Convert to TelemetryData model
            telemetry = TelemetryData(
                device_id=payload["device_id"],
                timestamp=datetime.fromisoformat(payload["timestamp"]),
                env_temperature=payload["env_temperature"],
                humidity=payload["humidity"],
                pressure=payload["pressure"],
                light=payload["light"],
                co2=payload["co2"],
                voc=payload["voc"],
                soil_temperature=payload["soil_temperature"],
                soil_moisture=payload["soil_moisture"],
                soil_ph=payload["soil_ph"]
            )

            # Store in database
            await data_store.add_telemetry(telemetry)

            # Notify WebSocket subscribers
            await self._notify_subscribers(topic, payload) #ERROR??? SHould be to websocket

            logger.debug(f"Processes telemetry for device {telemetry.device_id}")

        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")

    async def _handle_status(self, topic: str, payload: Dict):
        """Handle secice status updates"""
        try:
            device_id = payload["device_id"]
            status = payload["status"]

            # Update device status in database
            from app.services.database import db_service
            from app.models.device import DeviceStatus

            await db_service.update_device_status(device_id, DeviceStatus(status))

            logger.info(f"Device {device_id} status updated to {status}")
        
        except Exception as e:
            logger.error(f"Error handling status update: {e}")
    
    async def publish(self, topic: str, payload: Dict):
        """Publish to MQTT topic. TODO: Use actual MQTT client"""
        logger.info(f"Publishing to {topic}: {payload}")

        # TODO: Replace with actual MQTT publish
        # await self.mqtt_client.publish(topic, json.dumps(payload))
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to MQTT topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        
        self.subscribers[topic].append(callback)
        logger.info(f"Subscribed to {topic}")

        # TODO: Actually subscribe with MQTT client
        # await self.mqtt_client.subscribe(topic)
    
    async def _simulate_mqtt_messages(self):
        """Simulate MQTT messages. TODO: Remove when actual MQTT is connected"""
        import random
        
        while self.connected:
            try:
                # Get all devices from database
                from app.services.database import db_service
                devices = await db_service.get_devices()

                # Simulate telemetry from online devices
                for device in devices:
                    if device.status == "online" and random.random() > 0.2:
                        device_id = device.id
                        topic = f"devices/{device_id}/telemetry"
                        
                        payload = {
                            "device_id": device_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "env_temperature": random.uniform(20, 30),
                            "humidity": random.uniform(50, 70),
                            "pressure": random.uniform(1000, 1020),
                            "light": random.uniform(0, 50000),
                            "co2": random.uniform(350, 450),
                            "voc": random.uniform(0, 500),
                            "soil_temperature": random.uniform(18, 28),
                            "soil_moisture": random.uniform(40, 80),
                            "soil_ph": random.uniform(6.0, 7.5)
                        }
                        
                        # Process as if it came from MQTT
                        await self._handle_telemetry(topic, payload)
                
                await asyncio.sleep(10)  # Simulate every 10 seconds

            except Exception as e:
                logger.error(f"Error in MQTT simulation: {e}")
                await asyncio.sleep(10)
    
    async def _notify_subscribers(self, topic: str, payload: Dict):
        """Notify all subscribers of a topic"""
        # Check exact topic match
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                asyncio.create_task(callback(topic, payload))
        
        # Check wildcard subscriptions
        for sub_topic, callbacks in self.subscribers.items():
            if self._topic_matches(sub_topic, topic):
                for callback in callbacks:
                    asyncio.create_task(callback(topic, payload))
    
    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if topic matches pattern with wildcards"""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) != len(topic_parts):
            return False
        
        for p, t in zip(pattern_parts, topic_parts):
            if p == '+':  # Single level wildcard
                continue
            elif p == '#':  # Multi-level wildcard
                return True
            elif p != t:
                return False
        
        return True
