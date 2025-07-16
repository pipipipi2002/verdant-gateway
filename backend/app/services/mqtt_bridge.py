import asyncio
import json
from typing import Callable, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MQTTBridge:
    """Bridge between MQTT and HTTP/WebSocket. TODO: Implement actual MQTT client"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.connected = False
        
    async def start(self):
        """Start MQTT connection. TODO: Connect to actual MQTT broker"""
        logger.info("Starting MQTT bridge (simulated)")
        self.connected = True
        
        # Simulate incoming messages
        asyncio.create_task(self._simulate_mqtt_messages())
    
    async def stop(self):
        """Stop MQTT connection"""
        self.connected = False
        logger.info("Stopped MQTT bridge")
    
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
    
    async def _simulate_mqtt_messages(self):
        """Simulate MQTT messages. TODO: Remove when actual MQTT is connected"""
        import random
        
        while self.connected:
            # Simulate telemetry from devices
            for i in range(1, 6):
                if random.random() > 0.8:  # 20% chance to skip
                    continue
                    
                device_id = f"device-{i:03d}"
                topic = f"devices/{device_id}/telemetry"
                
                payload = {
                    "device_id": device_id,
                    "timestamp": datetime.now().isoformat(),
                    "soil_humidity": random.uniform(40, 80),
                    "soil_temperature": random.uniform(20, 30),
                    "co2": random.uniform(350, 450),
                    "device_temperature": random.uniform(25, 35),
                    "device_humidity": random.uniform(50, 70),
                    "status": "normal"
                }
                
                # Notify subscribers
                await self._notify_subscribers(topic, payload)
            
            await asyncio.sleep(10)  # Simulate every 10 seconds
    
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
