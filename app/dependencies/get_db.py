from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionLocal


async def get_db():
    db: AsyncSession = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
