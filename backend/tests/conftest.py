"""Test configuration and fixtures."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_session
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create a test database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')

    # Override the database URL for testing
    test_database_url = f"sqlite+aiosqlite:///{db_path}"

    # Create the test engine
    engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False}
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Override the get_session dependency
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = override_get_session

    yield engine

    # Cleanup
    await engine.dispose()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
async def client(test_db):
    """Create a test client."""
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def db_session(test_db):
    """Create a database session for testing."""
    async_session = async_sessionmaker(bind=test_db, expire_on_commit=False)
    async with async_session() as session:
        yield session
