from sqlalchemy.ext.asyncio import AsyncSession

from users.models.user import User
from users.schemas.create import Create as UserCreateSchema


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_create: UserCreateSchema) -> User:
        user = User(
            email=user_create.email,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            picture=user_create.picture,
            oauth_id=user_create.oauth_id,
            timezone=user_create.timezone,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def find_by_id(self, id: int) -> User | None:
        return await self.db.get(User, id)

    async def find_by_email(self, email: str) -> User | None:
        return await self.db.get(User, email)
