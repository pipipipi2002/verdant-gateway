import asyncio
import json
import logging
import uuid
from typing import Callable, Dict, List, Optional
from datetime import datetime, timezone, timedelta
import paho.mqtt.client as mqtt
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.models.telemetry import TelemetryData
from app.models.device import DeviceStatusData, DeviceStatus 
from app.services.data_store import data_store

logger = logging.getLogger(__name__)

class MQTTClient:
    """Real MQTT client implementation using paho-mqtt"""
    
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.subscribers: Dict[str, List[Callable]] = {}
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.device_status_cache: Dict[str, Dict] = {} # In-memory cache for real-time status
        
    async def start(self):
        """Start MQTT client and connect to broker"""
        try:
            self._loop = asyncio.get_event_loop()
            
            # Create MQTT client
            self.client = mqtt.Client(client_id=f"{settings.gateway_id}-backend")
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            
            # Configure client
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)
            
            # Configure authentication
            self.client.username_pw_set(settings.mqtt_user, settings.mqtt_pass)
            
            # TODO: Add TLS if needed
            # self.client.tls_set(ca_certs="ca.crt", certfile="client.crt", keyfile="client.key")
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}")
            self.client.connect_async(settings.mqtt_broker, settings.mqtt_port, keepalive=60)
            
            # Start the MQTT loop in a separate thread
            self.client.loop_start()
            
            # Wait a bit for connection
            await asyncio.sleep(2)
            
            # Subscribe to all device topics
            await self.subscribe("devices/+/telemetry", self._handle_telemetry)
            await self.subscribe("devices/+/status", self._handle_status)
            await self.subscribe("devices/+/alerts", self._handle_alerts)
            await self.subscribe("devices/discovery/announce", self._handle_discovery)
            
            logger.info("MQTT client started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            raise

    async def stop(self):
        """Stop MQTT client"""
        if self.client:
            logger.info("Stopping MQTT client")
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
        
        self.executor.shutdown(wait=True)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker successfully")
            
            # Re-subscribe to all topics on reconnect
            for topic in self.subscribers.keys():
                client.subscribe(topic, qos=1)
                logger.info(f"Re-subscribed to {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. RC: {rc}")
            self.connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. RC: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is acknowledged"""
        logger.debug(f"Subscription acknowledged. MID: {mid}, QoS: {granted_qos}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            logger.debug(f"Received message on {topic}: {payload}")
            
            # Run async handlers in the event loop
            if self._loop:
                asyncio.run_coroutine_threadsafe(
                    self._process_message(topic, payload),
                    self._loop
                )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message on {topic}: {e}")
        except Exception as e:
            logger.error(f"Error processing message on {topic}: {e}")
    
    async def _process_message(self, topic: str, payload: Dict):
        """Process incoming MQTT message"""
        # Check exact topic match
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    await callback(topic, payload)
                except Exception as e:
                    logger.error(f"Error in callback for {topic}: {e}")
        
        # Check wildcard subscriptions
        for sub_topic, callbacks in self.subscribers.items():
            if self._topic_matches(sub_topic, topic):
                for callback in callbacks:
                    try:
                        await callback(topic, payload)
                    except Exception as e:
                        logger.error(f"Error in wildcard callback for {topic}: {e}")
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to MQTT topic with callback"""
        # Store callback
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        
        # Actually subscribe with MQTT client
        if self.client and self.connected:
            self.client.subscribe(topic, qos=1)
            logger.info(f"Subscribed to MQTT topic: {topic}")
        else:
            logger.warning(f"Not connected, will subscribe to {topic} on connect")
    
    async def publish(self, topic: str, payload: Dict, qos: int = 1, retain: bool = False):
        """Publish message to MQTT topic"""
        if not self.client or not self.connected:
            logger.error(f"Cannot publish to {topic}: Not connected to MQTT broker")
            return False
        
        logger.info(f"Publishing to {topic} with qos {qos}")
        
        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}. RC: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    async def _handle_telemetry(self, topic: str, payload: Dict):
        """Handle incoming telemetry data"""
        try:
            # Extract device_id from topic or payload
            device_id = payload.get("device_id")
            if not device_id and "/" in topic:
                # Extract from topic: devices/{device_id}/telemetry
                parts = topic.split("/")
                if len(parts) >= 3:
                    device_id = parts[1]
            
            if not device_id:
                logger.error(f"No device_id found in telemetry message")
                return
            
            # Convert to TelemetryData model
            telemetry = TelemetryData(
                device_id=device_id,
                timestamp=datetime.fromisoformat(payload["timestamp"]) if "timestamp" in payload else datetime.now(timezone.utc),
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

            logger.info(f"Received MQTT Telemetry from device {device_id} of time {telemetry.timestamp}")
            
            # Store in database
            await data_store.add_telemetry(telemetry)
            
            # Notify WebSocket subscribers
            from app.main import websocket_manager
            if websocket_manager:
                await websocket_manager.broadcast_telemetry(device_id, payload)
            
            logger.info(f"Processed telemetry for device {device_id}")
            
        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")
    
    async def _handle_status(self, topic: str, payload: Dict):
        """Handle device status updates"""
        try:
            device_id = payload.get("device_id")
            if not device_id and "/" in topic:
                parts = topic.split("/")
                if len(parts) >= 3:
                    device_id = parts[1]

            if not device_id:
                logger.error(f"No device_id found in status message")
                return
            
            # Update in-memory cache for real-time display
            self.device_status_cache[device_id] = payload

            # Convert to DeviceStatusData model
            status_data = DeviceStatusData(
                device_id=device_id,
                timestamp=datetime.fromisoformat(payload["timestamp"]) if "timestamp" in payload else datetime.now(timezone.utc),
                status=payload.get("status", "offline"),
                firmware_version=payload.get("firmware_version", ""),
                uptime_seconds=payload.get("uptime_seconds", 0),
                rssi=payload.get("rssi", 0),
                error_code=payload.get("error_code", 0),
                error_message=payload.get("error_message", ""),
                free_memory=payload.get("free_memory"),
                internal_temperature=payload.get("internal_temperature", 0.0),
                internal_humidity=payload.get("internal_humidity", 0.0),
                battery_level=payload.get("battery_level")
            )

            # Store in database for history
            from app.services.database import db_service
            await db_service.add_device_status(status_data)

            # Notify Websocket subscribers
            from app.main import websocket_manager
            if websocket_manager:
                await websocket_manager.broadcast_status(device_id, payload)

            logger.info(f"Device {device_id} status updated: {status_data.status}")
            
        except Exception as e:
            logger.error(f"Error handling status update: {e}")
    
    async def _handle_alerts(self, topic: str, payload: Dict):
        """Handle device alerts"""
        try:
            device_id = payload.get("device_id")
            alert_type = payload.get("alert_type")
            severity = payload.get("severity")
            
            logger.warning(f"Alert from {device_id}: {alert_type} ({severity})")
            
            # TODO: Store alerts in database
            # TODO: Send notifications
            # TODO: Trigger automated responses
            
        except Exception as e:
            logger.error(f"Error handling alert: {e}")
    
    async def _handle_discovery(self, topic: str, payload: Dict):
        """Handle device discovery announcements"""
        try:
            device_id = payload.get("device_id")
            device_type = payload.get("device_type")
            
            logger.info(f"Device discovery: {device_id} ({device_type})")
            
            # Send discovery response
            await self.publish(
                f"devices/discovery/response/{device_id}",
                {
                    "device_id": device_id,
                    "accepted": True,
                    "gateway_id": settings.gateway_id,
                    "mqtt_topics": {
                        "telemetry": f"devices/{device_id}/telemetry",
                        "commands": f"devices/{device_id}/commands",
                        "config": f"devices/{device_id}/config"
                    },
                    "ntp_server": "gateway.local",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # TODO: Register device in database
            
        except Exception as e:
            logger.error(f"Error handling discovery: {e}")
    
    async def send_gateway_ping(self):
        ping_payload = {
            "gateway_id": settings.gateway_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": str(uuid.uuid64()),
            "type:": "status_request"
        }

        await self.publish("gateway/ping", ping_payload, qos=1, retain=False)
        logger.info(f"Sent gateway ping: {ping_payload['request_id']}")

        asyncio.create_task(self._cleanup_old_status())


    def _topic_matches(self, pattern: str, topic: str) -> bool:
        """Check if topic matches pattern with wildcards"""
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if len(pattern_parts) != len(topic_parts) and '#' not in pattern:
            return False
        
        for i, (p, t) in enumerate(zip(pattern_parts, topic_parts)):
            if p == '+':  # Single level wildcard
                continue
            elif p == '#':  # Multi-level wildcard
                return True
            elif p != t:
                return False
        
        return True
    
    async def _cleanup_old_status(self):
        """Remove devices that don't respond to ping after timeout"""
        await asyncio.sleep(10)  # Wait for responses
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        offline_devices = []
        
        for device_id, status in self.device_status_cache.items():
            status_time = datetime.fromisoformat(status.get("timestamp", "2000-01-01T00:00:00Z"))
            if status_time < cutoff_time:
                offline_devices.append(device_id)
        
        # Mark devices as offline if they didn't respond
        for device_id in offline_devices:
            self.device_status_cache[device_id] = {
                "device_id": device_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "offline",
                "error_code": 99,
                "error_message": "No response to gateway ping"
            }
            logger.warning(f"Device {device_id} marked offline - no ping response")


# Global instance
mqtt_client = MQTTClient()