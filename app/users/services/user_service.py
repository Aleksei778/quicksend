from typing import Annotated
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.database import get_db
from users.models.user import User
from users.schemas.find_or_create_user import FindOrCreateUser


class UserService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def find_or_create_user(self, find_or_create_dto: FindOrCreateUser) -> User:
        user = await self.find_by_email(email=find_or_create_dto.email)

        if not user:
            user = await self._create(
                FindOrCreateUser(
                    email=find_or_create_dto.email,
                    first_name=find_or_create_dto.first_name,
                    last_name=find_or_create_dto.last_name,
                    picture=find_or_create_dto.picture,
                    oauth_id=find_or_create_dto.oauth_id,
                )
            )

        return user

    async def _create(self, find_or_create_dto: FindOrCreateUser) -> User:
        user = User(
            email=find_or_create_dto.email,
            first_name=find_or_create_dto.first_name,
            last_name=find_or_create_dto.last_name,
            picture=find_or_create_dto.picture,
            oauth_id=find_or_create_dto.oauth_id,
        )

        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        return user

    async def find_by_id(self, user_id: int) -> User | None:
        return await self._db.get(User, user_id)

    async def find_by_email(self, email: EmailStr) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))

        return result.scalar_one_or_none()

    async def get_user_info_for_jwt(self, user: User) -> dict[str, str]:
        return {
            "user_id": user.id,
            "email": user.email,
            "oauth_id": user.oauth_id
        }


async def get_user_service(db: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(db=db)
