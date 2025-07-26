"""
Development server runner for the Plant Monitoring System
"""
import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.logging_config import setup_logging
from app.config import settings

logger = setup_logging(settings.log_level)

if __name__ == "__main__":
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(name)s - %(levelname)s - %(client_addr)s - "%(request_line)s" %(status_code)s'

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=log_config,
        log_level=settings.log_level.lower()
    )
