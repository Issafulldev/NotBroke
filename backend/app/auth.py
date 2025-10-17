"""Authentication utilities using JWT tokens."""

from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from . import models
from .database import get_session

# Validation sécurisée des variables d'environnement critiques
def validate_environment():
    """Valider et configurer les variables d'environnement critiques."""
    environment = os.getenv("ENVIRONMENT", "development")

    # SECRET_KEY validation
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        if environment == "production":
            raise ValueError(
                "SECRET_KEY environment variable must be set in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        else:
            # En développement seulement, générer une clé temporaire
            secret_key = secrets.token_urlsafe(32)
            print("⚠️  WARNING: Using generated SECRET_KEY. This is NOT secure for production!")
            print("   Set SECRET_KEY environment variable for production use.")

    # ACCESS_TOKEN_EXPIRE_MINUTES validation
    try:
        expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        if expire_minutes < 5:
            print("⚠️  WARNING: ACCESS_TOKEN_EXPIRE_MINUTES is very low (< 5 minutes)")
        elif expire_minutes > 1440:  # 24 heures
            print("⚠️  WARNING: ACCESS_TOKEN_EXPIRE_MINUTES is very high (> 24 hours)")
    except ValueError:
        raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer")

    return secret_key, expire_minutes

# Configuration des variables validées
SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES = validate_environment()
ALGORITHM = "HS256"

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session = Depends(get_session),
) -> models.User:
    """Get the current authenticated user from JWT token."""
    from . import crud

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Récupérer l'utilisateur depuis la base
    user = await crud.get_user_by_username(session, username)
    if user is None:
        raise credentials_exception
    return user


# Dependency for optional authentication (returns None if not authenticated)
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session = Depends(get_session),
) -> models.User | None:
    """Get the current authenticated user, or None if not authenticated."""
    from . import crud

    if credentials is None:
        return None

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    # Récupérer l'utilisateur depuis la base
    user = await crud.get_user_by_username(session, username)
    return user
