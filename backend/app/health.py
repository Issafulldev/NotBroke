"""Health check endpoint with detailed system information."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

from fastapi import Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_session, engine
from . import __version__


async def check_database_health(session: AsyncSession) -> dict[str, Any]:
    """Check database connectivity and health."""
    try:
        # Test database connection
        result = await session.execute(text("SELECT 1"))
        result.scalar()
        
        # Get database version if PostgreSQL
        db_info = {"status": "healthy", "type": "unknown"}
        try:
            # Try PostgreSQL version query
            version_result = await session.execute(text("SELECT version()"))
            version = version_result.scalar()
            db_info["type"] = "postgresql"
            db_info["version"] = version.split(",")[0] if version else "unknown"
        except Exception:
            # Try SQLite version query
            try:
                version_result = await session.execute(text("SELECT sqlite_version()"))
                version = version_result.scalar()
                db_info["type"] = "sqlite"
                db_info["version"] = version or "unknown"
            except Exception:
                pass
        
        return db_info
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "type": "unknown"
        }


async def get_health_status(
    include_details: bool = Query(False, description="Include detailed system information"),
    session: AsyncSession = Depends(get_session)
) -> JSONResponse:
    """
    Health check endpoint with optional detailed system information.
    
    - **include_details**: Include detailed system information (default: False)
    """
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": __version__,
    }
    
    # Check database health
    db_health = await check_database_health(session)
    health_status["database"] = db_health
    
    # Determine overall status
    overall_status = "ok"
    if db_health.get("status") == "unhealthy":
        overall_status = "degraded"
    
    health_status["status"] = overall_status
    
    # Include detailed information if requested
    if include_details:
        health_status["system"] = {
            "python_version": sys.version.split()[0],
            "platform": sys.platform,
        }
        
        # Database pool info
        pool = engine.pool
        health_status["database"]["pool"] = {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        }
    
    # Set appropriate HTTP status code
    http_status = status.HTTP_200_OK if overall_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(content=health_status, status_code=http_status)

