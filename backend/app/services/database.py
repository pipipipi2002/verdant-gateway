import asyncio
import asyncpg
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import logging

from app.config import settings
from app.models.telemetry import TelemetryData
from app.models.device import Device, DeviceStatus, DeviceStatusData
from app.models.farm import Farm

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for interacting with TimescaleDB"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self):
        """Connect to the database"""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                min_size=10,
                max_size=20
            )
            logger.info("Connected to TimescaleDB")
            
            # Initialize schema
            await self._init_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.pool:
            try:
                # Close pool with timeout
                await asyncio.wait_for(self.pool.close(), timeout=5.0)
                logger.info("Disconnected from TimescaleDB")
            except asyncio.TimeoutError:
                logger.warning("Database pool close timed out - terminating connections")
                self.pool.terminate()
            except Exception as e:
                logger.error(f"Error closing database pool: {e}")
                self.pool.terminate()
    
    async def _init_schema(self):
        """Initialize database schema"""
        async with self.pool.acquire() as conn:
            # Create tables
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS farms (
                    id VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    location VARCHAR(255),
                    gateway_id VARCHAR(50),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id VARCHAR(50) PRIMARY KEY,
                    farm_id VARCHAR(50) REFERENCES farms(id),
                    name VARCHAR(255) NOT NULL,
                    plant_name VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'offline',
                    last_seen TIMESTAMPTZ,
                    telemetry_interval INTEGER DEFAULT 60,
                    snapshot_interval INTEGER DEFAULT 3600,
                    location VARCHAR(255),
                    firmware_version VARCHAR(50),
                    ip_address VARCHAR(45),
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS telemetry (
                    device_id VARCHAR(50) REFERENCES devices(id),
                    timestamp TIMESTAMPTZ NOT NULL,
                    env_temperature DOUBLE PRECISION,
                    humidity DOUBLE PRECISION,
                    pressure DOUBLE PRECISION,
                    light DOUBLE PRECISION,
                    co2 DOUBLE PRECISION,
                    voc DOUBLE PRECISION,
                    soil_temperature DOUBLE PRECISION,
                    soil_moisture DOUBLE PRECISION,
                    soil_ph DOUBLE PRECISION,
                    PRIMARY KEY (device_id, timestamp)
                )
            ''')
            
            # Convert telemetry table to hypertable
            await conn.execute('''
                SELECT create_hypertable('telemetry', 'timestamp', 
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                )
            ''')
            
            # Create device status table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS device_status (
                    device_id VARCHAR(50) REFERENCES devices(id),
                    timestamp TIMESTAMPTZ NOT NULL,
                    status VARCHAR(20),
                    firmware_version VARCHAR(50),
                    uptime_seconds INTEGER,
                    rssi INTEGER,
                    error_code INTEGER,
                    error_message TEXT,
                    free_memory BIGINT,
                    internal_temperature DOUBLE PRECISION,
                    internal_humidity DOUBLE PRECISION,
                    battery_level INTEGER,
                    PRIMARY KEY (device_id, timestamp)
                )
            ''')
            
            # Convert to hypertable
            await conn.execute('''
                SELECT create_hypertable('device_status', 'timestamp', 
                    if_not_exists => TRUE,
                    chunk_time_interval => INTERVAL '1 day'
                )
            ''')
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_telemetry_device_time 
                ON telemetry (device_id, timestamp DESC)
            ''')
            
            # Create continuous aggregate for hourly averages
            await conn.execute('''
                CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_hourly
                WITH (timescaledb.continuous) AS
                SELECT 
                    device_id,
                    time_bucket('1 hour', timestamp) AS hour,
                    AVG(env_temperature) as avg_env_temperature,
                    AVG(humidity) as avg_humidity,
                    AVG(pressure) as avg_pressure,
                    AVG(light) as avg_light,
                    AVG(co2) as avg_co2,
                    AVG(voc) as avg_voc,
                    AVG(soil_temperature) as avg_soil_temperature,
                    AVG(soil_moisture) as avg_soil_moisture,
                    AVG(soil_ph) as avg_soil_ph,
                    COUNT(*) as sample_count
                FROM telemetry
                GROUP BY device_id, hour
                WITH NO DATA
            ''')
            
            logger.info("Database schema initialized")
    
    async def populate_dummy_data(self):
        """Populate database with dummy data for testing"""
        try:
            # Check if data already exists
            async with self.pool.acquire() as conn:
                farm_count = await conn.fetchval("SELECT COUNT(*) FROM farms")
                if farm_count > 0:
                    logger.info("Database already has data, skipping population")
                    return
            
            # Create farm
            farm = Farm(
                id="farm-001",
                name="Green Acres Plantation",
                location="Jurong West, Singapore",
                device_count=5,
                active_devices=4,
                offline_devices=1,
                connection_status="local",
                gateway_id="gateway-001",
                created_at=datetime.now(timezone.utc) - timedelta(days=30),
                updated_at=datetime.now(timezone.utc)
            )
            
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO farms (id, name, location, gateway_id, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''', farm.id, farm.name, farm.location, farm.gateway_id, farm.created_at, farm.updated_at)
            
            # Create devices
            plant_names = ["Tomato A1", "Lettuce B2", "Basil C3", "Pepper D4", "Spinach E5"]
            devices = []
            
            for i in range(5):
                device = Device(
                    id=f"device-{i+1:03d}",
                    farm_id="farm-001",
                    name=f"Sensor Unit {i+1}",
                    plant_name=plant_names[i],
                    status=DeviceStatus.OFFLINE if i == 4 else DeviceStatus.ONLINE,
                    last_seen=datetime.now(timezone.utc) - timedelta(minutes=5 if i != 4 else 120),
                    telemetry_interval=60,
                    snapshot_interval=3600,
                    location=f"Row {i//2 + 1}, Position {i%2 + 1}",
                    firmware_version="1.0.0",
                    ip_address=f"192.168.1.{100+i}" if i != 4 else None
                )
                devices.append(device)
                
                async with self.pool.acquire() as conn:
                    await conn.execute('''
                        INSERT INTO devices (id, farm_id, name, plant_name, status, last_seen, 
                                           telemetry_interval, snapshot_interval, location, firmware_version, ip_address)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ''', device.id, device.farm_id, device.name, device.plant_name, 
                        device.status.value, device.last_seen, device.telemetry_interval,
                        device.snapshot_interval, device.location, device.firmware_version, device.ip_address)
            
            # Generate historical telemetry in batches for better performance
            import random
            batch_size = 100
            telemetry_batch = []
            
            for device in devices[:4]:  # Only for online devices
                # Add current device status
                status = DeviceStatusData(
                    device_id=device.id,
                    timestamp=datetime.now(timezone.utc),
                    status=DeviceStatus.ONLINE,
                    firmware_version=device.firmware_version,
                    uptime_seconds=random.randint(3600, 86400),
                    rssi=random.randint(-80, -40),
                    error_code=0,
                    error_message="",
                    free_memory=random.randint(50000, 200000),
                    internal_temperature=random.uniform(25, 35),
                    internal_humidity=random.uniform(30, 50),
                    battery_level=random.randint(70, 100) if i % 2 == 0 else None
                )
                await self.add_device_status(status)

                for hours_ago in range(24, 0, -1):
                    telemetry = TelemetryData(
                        device_id=device.id,
                        timestamp=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
                        env_temperature=random.uniform(20, 30),
                        humidity=random.uniform(50, 70),
                        pressure=random.uniform(1000, 1020),
                        light=random.uniform(0, 50000),
                        co2=random.uniform(350, 450),
                        voc=random.uniform(0, 500),
                        soil_temperature=random.uniform(18, 28),
                        soil_moisture=random.uniform(40, 80),
                        soil_ph=random.uniform(6.0, 7.5)
                    )
                    telemetry_batch.append(telemetry)
                    
                    if len(telemetry_batch) >= batch_size:
                        await self._insert_telemetry_batch(telemetry_batch)
                        telemetry_batch = []
            
            # Insert remaining telemetry
            if telemetry_batch:
                await self._insert_telemetry_batch(telemetry_batch)
            
            logger.info("Database populated with dummy data")
            
        except Exception as e:
            logger.error(f"Failed to populate dummy data: {e}")
            raise
    
    async def _insert_telemetry_batch(self, telemetry_batch: List[TelemetryData]):
        """Insert telemetry data in batch for better performance"""
        async with self.pool.acquire() as conn:
            await conn.executemany('''
                INSERT INTO telemetry (device_id, timestamp, env_temperature, humidity,
                                         pressure, light, co2, voc, soil_temperature, 
                                         soil_moisture, soil_ph)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ''', [(t.device_id, t.timestamp, t.env_temperature, t.humidity,
                   t.pressure, t.light, t.co2, t.voc, t.soil_temperature, t.soil_moisture, t.soil_ph) 
                  for t in telemetry_batch])
    
    # Telemetry operations
    async def add_telemetry(self, telemetry: TelemetryData):
        """Add telemetry data to the database"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO telemetry (device_id, timestamp, env_temperature, humidity,
                                         pressure, light, co2, voc, soil_temperature, 
                                         soil_moisture, soil_ph)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (device_id, timestamp) DO UPDATE SET
                        env_temperature = EXCLUDED.env_temperature,
                        humidity = EXCLUDED.humidity,
                        pressure = EXCLUDED.pressure,
                        light = EXCLUDED.light,
                        co2 = EXCLUDED.co2,
                        voc = EXCLUDED.voc,
                        soil_temperature = EXCLUDED.soil_temperature,
                        soil_moisture = EXCLUDED.soil_moisture,
                        soil_ph = EXCLUDED.soil_ph
                ''', telemetry.device_id, telemetry.timestamp, telemetry.env_temperature,
                    telemetry.humidity, telemetry.pressure, telemetry.light, telemetry.co2,
                    telemetry.voc, telemetry.soil_temperature, telemetry.soil_moisture,
                    telemetry.soil_ph)
                
                # Update device last_seen
                await conn.execute('''
                    UPDATE devices 
                    SET last_seen = $1
                    WHERE id = $2
                ''', telemetry.timestamp, telemetry.device_id)
            except Exception as e:
                logger.error(f"Error adding telemetry: {e}")
                raise
    
    async def get_latest_telemetry(self, device_id: str) -> Optional[TelemetryData]:
        """Get the latest telemetry for a device"""
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT * FROM telemetry 
                    WHERE device_id = $1 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', device_id)
                
                if row:
                    return TelemetryData(**dict(row))
                return None
            except Exception as e:
                logger.error(f"Error getting latest telemetry: {e}")
                return None
    
    async def get_telemetry_history(self, device_id: str, hours: int = 24) -> List[TelemetryData]:
        """Get telemetry history for a device"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch('''
                    SELECT * FROM telemetry 
                    WHERE device_id = $1 AND timestamp > $2
                    ORDER BY timestamp DESC
                ''', device_id, cutoff)
                
                return [TelemetryData(**dict(row)) for row in rows]
            except Exception as e:
                logger.error(f"Error getting telemetry history: {e}")
                return []
    
    # Device operations
    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM devices WHERE id = $1
            ''', device_id)
            
            if row:
                device_dict = dict(row)
                device_dict['status'] = DeviceStatus(device_dict['status'])
                return Device(**device_dict)
            return None
    
    async def get_devices(self, farm_id: Optional[str] = None) -> List[Device]:
        """Get all devices, optionally filtered by farm"""
        async with self.pool.acquire() as conn:
            if farm_id:
                rows = await conn.fetch('''
                    SELECT * FROM devices WHERE farm_id = $1
                ''', farm_id)
            else:
                rows = await conn.fetch('SELECT * FROM devices')
            
            devices = []
            for row in rows:
                device_dict = dict(row)
                device_dict['status'] = DeviceStatus(device_dict['status'])
                devices.append(Device(**device_dict))
            
            return devices
    
    async def update_device_status(self, device_id: str, status: DeviceStatus):
        """Update device status"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE devices 
                SET updated_at = NOW()
                WHERE id = $1
            ''', device_id)
    
    async def add_device_status(self, status: DeviceStatusData):
        """Add device status to time-series table"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO device_status (device_id, timestamp, status, firmware_version,
                                             uptime_seconds, rssi, error_code,
                                             error_message, free_memory, internal_temperature,
                                             internal_humidity, battery_level)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ''', status.device_id, status.timestamp, status.status, status.firmware_version,
                    status.uptime_seconds, status.rssi, status.error_code,
                    status.error_message, status.free_memory, status.internal_temperature,
                    status.internal_humidity, status.battery_level)
            except Exception as e:
                logger.error(f"Error adding device status: {e}")
                raise
    
    async def get_latest_device_status(self, device_id: str) -> Optional[DeviceStatusData]:
        """Get the latest status for a device"""
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow('''
                    SELECT * FROM device_status 
                    WHERE device_id = $1 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''', device_id)
                
                if row:
                    return DeviceStatusData(**dict(row))
                return None
            except Exception as e:
                logger.error(f"Error getting latest device status: {e}")
                return None
    
    async def update_device_ip(self, device_id: str, ip_address: str):
        """Update device IP address"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE devices
                SET ip_address = $1, updated_at = NOW()
                WHERE id = $2               
                ''', ip_address, device_id)

    async def register_device(self, device: Device) -> bool:
        """Register a new device or update existing one"""
        async with self.pool.acquire() as conn:
            try:
                # Try to insert or update on conflict
                await conn.execute('''
                    INSERT INTO devices (id, farm_id, name, plant_name, status, last_seen,
                                       telemetry_interval, snapshot_interval, location, 
                                       firmware_version, ip_address, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        plant_name = EXCLUDED.plant_name,
                        status = EXCLUDED.status,
                        last_seen = EXCLUDED.last_seen,
                        telemetry_interval = EXCLUDED.telemetry_interval,
                        snapshot_interval = EXCLUDED.snapshot_interval,
                        location = EXCLUDED.location,
                        firmware_version = EXCLUDED.firmware_version,
                        ip_address = EXCLUDED.ip_address,
                        updated_at = NOW()
                ''', device.id, device.farm_id, device.name, device.plant_name,
                    device.status.value, device.last_seen, device.telemetry_interval,
                    device.snapshot_interval, device.location, device.firmware_version,
                    device.ip_address)
                
                logger.info(f"Device {device.id} registered successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error registering device {device.id}: {e}")
                return False

    # Farm operations
    async def get_farm(self, farm_id: str) -> Optional[Farm]:
        """Get farm by ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT f.*,
                    COUNT(d.id) as device_count,
                    COUNT(CASE WHEN d.status = 'online' THEN 1 END) as active_devices,
                    COUNT(CASE WHEN d.status = 'offline' THEN 1 END) as offline_devices
                FROM farms f
                LEFT JOIN devices d ON f.id = d.farm_id
                WHERE f.id = $1
                GROUP BY f.id
            ''', farm_id)
            
            if row:
                farm_dict = dict(row)
                farm_dict['connection_status'] = 'local'  # TODO: Determine from actual connection
                return Farm(**farm_dict)
            return None
    
    async def get_farms(self) -> List[Farm]:
        """Get all farms"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT f.*,
                    COUNT(d.id) as device_count,
                    COUNT(CASE WHEN d.status = 'online' THEN 1 END) as active_devices,
                    COUNT(CASE WHEN d.status = 'offline' THEN 1 END) as offline_devices
                FROM farms f
                LEFT JOIN devices d ON f.id = d.farm_id
                GROUP BY f.id
            ''')
            
            farms = []
            for row in rows:
                farm_dict = dict(row)
                farm_dict['connection_status'] = 'local'  # TODO: Determine from actual connection
                farms.append(Farm(**farm_dict))
            
            return farms

# Global instance
db_service = DatabaseService()