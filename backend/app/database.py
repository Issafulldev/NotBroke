"""Database configuration and helpers for the expense platform backend."""

from collections.abc import AsyncIterator
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./expense.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


# Détecter si on est en production
try:
    from .config import config
    is_production = config.is_production
except Exception:
    # Fallback si config n'est pas disponible
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

# Optimisations pour production (Render)
if is_production and "postgresql" in DATABASE_URL:
    # Configuration optimisée pour PostgreSQL sur Render
    connect_args = {
        "command_timeout": 60,  # Timeout pour les commandes SQL (60 secondes)
        "server_settings": {
            "application_name": "notbroke_backend",
            "tcp_user_timeout": "60000",  # 60 secondes en millisecondes
        }
    }
    pool_size = 10  # Plus de connexions en production
    max_overflow = 20
    pool_recycle = 1800  # 30 minutes (Render peut réutiliser les connexions)
else:
    # Configuration pour développement ou SQLite
    connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    pool_size = 5
    max_overflow = 10
    pool_recycle = 300  # 5 minutes en développement

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Désactiver les logs SQL en production
    future=True,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_pre_ping=True,  # Vérifier les connexions avant utilisation
    pool_recycle=pool_recycle,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope for database operations."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create database tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

