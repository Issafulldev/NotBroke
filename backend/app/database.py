"""Database configuration and helpers for the expense platform backend."""

from collections.abc import AsyncIterator
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./expense.db")


# Optimisations pour production
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Désactiver les logs SQL en production
    future=True,
    pool_size=5,  # Limiter la taille du pool pour économiser la mémoire
    max_overflow=10,  # Nombre maximum de connexions supplémentaires
    pool_pre_ping=True,  # Vérifier les connexions avant utilisation
    pool_recycle=300,  # Recycler les connexions après 5 minutes
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
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

