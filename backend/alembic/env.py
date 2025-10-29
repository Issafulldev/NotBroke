"""Alembic migration environment for async SQLAlchemy."""

from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import your models and database configuration
from app.database import Base
from app.models import User, Category, Expense, Translation  # noqa: F401
from app.config import config

# this is the Alembic Config object
alembic_config = context.config

# Interpret the config file for Python logging.
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Set the sqlalchemy.url from environment variable
database_url = config.get("DATABASE_URL", "sqlite+aiosqlite:///./expense.db")
# Convert async URL to sync URL for Alembic
if database_url.startswith("sqlite+aiosqlite"):
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite+pysqlite")
elif database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

alembic_config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = alembic_config.get_section(alembic_config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url.replace("+psycopg2", "+asyncpg").replace("+pysqlite", "+aiosqlite")
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio

    asyncio.run(run_migrations_online())

