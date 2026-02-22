"""Alembic migration environment configuration."""
from logging.config import fileConfig
from urllib.parse import unquote

from sqlalchemy import pool, create_engine
from alembic import context

# Import Base and models (metadata only — no async engine created here)
from sqlalchemy.orm import declarative_base
from app.models import models  # noqa: F401 – ensure models are registered
from app.db.base import Base  # Import standalone Base (no async engine)
from app.core.config import settings

config = context.config

# Build a SYNC url for Alembic (psycopg2) from the async one
import os
_raw_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
_sync_url = _raw_url.replace("+asyncpg", "").replace("+aiosqlite", "")
# Note: do NOT unquote — psycopg2 handles percent-encoded passwords correctly
config.set_main_option("sqlalchemy.url", _sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Create a sync engine explicitly using psycopg2
    sync_url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(sync_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
