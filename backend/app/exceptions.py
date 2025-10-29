"""Global exception handlers for the FastAPI application."""

from __future__ import annotations

import logging
import os
import traceback
from typing import Any

from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud

logger = logging.getLogger(__name__)


def get_cors_headers(request: Request) -> dict[str, str]:
    """Get CORS headers for a request."""
    # Import here to avoid circular imports
    from .main import ALLOWED_ORIGINS
    
    origin = request.headers.get("origin")
    normalized_origin = origin.rstrip("/") if origin else None
    normalized_allowed = [o.rstrip("/") for o in ALLOWED_ORIGINS]

    headers = {
        "Access-Control-Allow-Credentials": "true",
    }

    # Vérifier si l'origine est autorisée
    if normalized_origin and normalized_origin in normalized_allowed:
        headers["Access-Control-Allow-Origin"] = origin
    elif ALLOWED_ORIGINS:
        # Utiliser la première origine autorisée si l'origine de la requête ne correspond pas
        headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGINS[0]
    
    return headers


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException with CORS headers."""
    cors_headers = get_cors_headers(request)
    
    # Merge CORS headers with any existing headers from the exception
    headers = {**cors_headers, **(exc.headers or {})}
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "http_error",
        },
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}", exc_info=True)
    cors_headers = get_cors_headers(request)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": str(exc),
            "type": "validation_error",
        },
        headers=cors_headers,
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle database integrity errors (unique constraints, foreign keys, etc.)."""
    error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    
    # Log the full error for debugging
    logger.error(f"Database integrity error: {error_msg}", exc_info=True)
    
    cors_headers = get_cors_headers(request)
    
    # Provide user-friendly error messages
    if "unique constraint" in error_msg.lower() or "duplicate" in error_msg.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "A resource with this information already exists",
                "type": "integrity_error",
            },
            headers=cors_headers,
        )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Database constraint violation",
            "type": "integrity_error",
        },
        headers=cors_headers,
    )


async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """Handle database operational errors (connection issues, etc.)."""
    error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    
    logger.error(f"Database operational error: {error_msg}", exc_info=True)
    
    cors_headers = get_cors_headers(request)
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database service temporarily unavailable. Please try again later.",
            "type": "database_error",
        },
        headers=cors_headers,
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions."""
    logger.warning(f"Value error: {str(exc)}", exc_info=True)
    
    cors_headers = get_cors_headers(request)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "type": "value_error",
        },
        headers=cors_headers,
    )


async def crud_error_handler(request: Request, exc: crud.CategoryNameConflictError | crud.UserAlreadyExistsError) -> JSONResponse:
    """Handle custom CRUD exceptions."""
    logger.warning(f"CRUD error: {str(exc)}")
    
    cors_headers = get_cors_headers(request)
    
    if isinstance(exc, crud.CategoryNameConflictError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, crud.UserAlreadyExistsError):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": str(exc),
            "type": "crud_error",
        },
        headers=cors_headers,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unhandled exceptions."""
    # Log full exception with traceback
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
        },
    )
    
    cors_headers = get_cors_headers(request)
    
    # In production, don't expose internal error details
    environment = os.getenv("ENVIRONMENT", "development")
    detail = str(exc) if environment == "development" else "An internal error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": detail,
            "type": "internal_error",
        },
        headers=cors_headers,
    )

