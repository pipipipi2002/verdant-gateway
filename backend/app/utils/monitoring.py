import asyncio
import psutil
from datetime import datetime, timezone
from typing import Dict

class GatewayMonitor:
    """Monitor gateway health metrics"""
    
    def __init__(self):
        self.metrics = {
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "disk_percent": 0.0,
            "network_io": {"sent": 0, "recv": 0},
            "uptime_hours": 0.0,
            "last_updated": datetime.now(timezone.utc)
        }
        self.start_time = datetime.now(timezone.utc)
        self._monitoring = False
    
    async def start_monitoring(self):
        """Start monitoring gateway metrics"""
        self._monitoring = True
        asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self._monitoring = False
    
    async def _monitor_loop(self):
        """Monitor system metrics periodically"""
        while self._monitoring:
            try:
                # CPU usage
                self.metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics["memory_percent"] = memory.percent
                
                # Disk usage
                disk = psutil.disk_usage('/')
                self.metrics["disk_percent"] = disk.percent
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.metrics["network_io"] = {
                    "sent": net_io.bytes_sent,
                    "recv": net_io.bytes_recv
                }
                
                # Uptime
                uptime = datetime.now(timezone.utc) - self.start_time
                self.metrics["uptime_hours"] = uptime.total_seconds() / 3600
                
                self.metrics["last_updated"] = datetime.now(timezone.utc)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            await asyncio.sleep(10)  # Update every 10 seconds
    
    async def get_metrics(self) -> Dict:
        """Get current metrics"""
        return self.metrics.copy()