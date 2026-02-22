import ssl as _ssl
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base  # noqa: F401 – re-exported for convenience

# SQLite needs check_same_thread=False; PostgreSQL doesn't use connect_args
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Ensure async driver prefix is present (Neon/Vercel gives plain postgresql://)
_raw_url = settings.DATABASE_URL
if _raw_url.startswith("postgresql://"):
    _raw_url = _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql+asyncpg://", 1)

# asyncpg doesn't support sslmode in URL — strip it and pass ssl via connect_args
_needs_ssl = "sslmode=require" in _raw_url or "ssl=true" in _raw_url
_async_url = (
    _raw_url
    .replace("?sslmode=require", "")
    .replace("&sslmode=require", "")
    .replace("?ssl=true", "")
    .replace("&ssl=true", "")
)

if _is_sqlite:
    _connect_args = {"check_same_thread": False}
elif _needs_ssl:
    _ssl_ctx = _ssl.create_default_context()
    _connect_args = {"ssl": _ssl_ctx}
else:
    _connect_args = {}

engine = create_async_engine(
    _async_url,
    echo=False,
    future=True,
    connect_args=_connect_args,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



async def get_db() -> AsyncSession:
    """Dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
