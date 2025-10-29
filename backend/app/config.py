"""Environment variable validation and configuration."""

from __future__ import annotations

import os
import secrets
from typing import Any

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class EnvironmentConfig:
    """Validate and provide access to environment variables."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.validate()
    
    def validate(self) -> None:
        """Validate critical environment variables."""
        errors: list[str] = []
        
        # Validate SECRET_KEY
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if self.environment == "production":
                errors.append(
                    "SECRET_KEY environment variable must be set in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            else:
                # Generate a temporary key for development
                os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)
                print("⚠️  WARNING: Using generated SECRET_KEY. This is NOT secure for production!")
                print("   Set SECRET_KEY environment variable for production use.")
        
        # Validate DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            errors.append("DATABASE_URL environment variable must be set")
        elif self.environment == "production":
            if "sqlite" in database_url.lower():
                errors.append(
                    "SQLite is not recommended for production. Use PostgreSQL instead."
                )
        
        # Validate FRONTEND_URL in production
        if self.environment == "production":
            frontend_url = os.getenv("FRONTEND_URL")
            if not frontend_url:
                errors.append(
                    "FRONTEND_URL environment variable must be set in production for CORS configuration"
                )
            elif not frontend_url.startswith(('http://', 'https://')):
                errors.append("FRONTEND_URL must be a valid HTTP/HTTPS URL")
        
        # Validate ACCESS_TOKEN_EXPIRE_MINUTES
        try:
            expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
            if expire_minutes < 5:
                print("⚠️  WARNING: ACCESS_TOKEN_EXPIRE_MINUTES is very low (< 5 minutes)")
            elif expire_minutes > 1440:  # 24 hours
                print("⚠️  WARNING: ACCESS_TOKEN_EXPIRE_MINUTES is very high (> 24 hours)")
        except ValueError:
            errors.append("ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer")
        
        if errors:
            error_msg = "\n".join(f"  - {error}" for error in errors)
            raise ValueError(f"Environment validation failed:\n{error_msg}")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get environment variable."""
        return os.getenv(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default


# Global configuration instance
config = EnvironmentConfig()

