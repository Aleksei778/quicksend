from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from common.utils.config import base_config

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{base_config.DB_USER}:"
    f"{base_config.DB_PASS}@"
    f"{base_config.DB_HOST}:"
    f"{base_config.DB_PORT}/"
    f"{base_config.DB_NAME}"
    f"?async_fallback=True"
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    future=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@asynccontextmanager
async def get_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


Base = declarative_base()
