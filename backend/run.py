"""
Development server runner for the Plant Monitoring System
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

# backend/app/__init__.py
"""Plant Monitoring System Backend"""
__version__ = "1.0.0"

# backend/app/api/__init__.py
# Empty file to make this a package

# backend/app/api/v1/__init__.py
# Empty file to make this a package

# backend/app/models/__init__.py
# Empty file to make this a package

# backend/app/services/__init__.py
# Empty file to make this a package

# backend/app/utils/__init__.py
# Empty file to make this a package