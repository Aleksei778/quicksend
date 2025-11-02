from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import SessionLocal
from repositories.user import UserRepository


async def get_db():
    db: AsyncSession = SessionLocal()
    try:
        yield db
    finally:
        await db.close()


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
