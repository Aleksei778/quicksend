from typing import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from common.config.base_config import base_settings


SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{base_settings.DB_USER}:"
    f"{base_settings.DB_PASS}@"
    f"{base_settings.DB_HOST}:"
    f"{base_settings.DB_PORT}/"
    f"{base_settings.DB_NAME}"
    f"?async_fallback=True"
)

# Создаем асинхронный движок
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
        finally:
            await session.close()


class Base(DeclarativeBase):
    pass
