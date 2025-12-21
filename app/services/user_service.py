from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple, Dict

from models.user import User
from models.subscription import Subscription
from schemas.user_schema import UserCreate

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user_create: UserCreate) -> User:
        user = User(
            email=user_create.email,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            picture=user_create.picture
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def find_user_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def find_user_by_email(self, email: str) -> User | None:
        return await self.db.get(User, email)

    async def get_user_subs(self, user_id: int) -> List[Subscription] | None:
        user = await self.find_user_by_id(user_id)

        if not user:
            return None

        return user.subscriptions

    async def is_user_already_used_trial(self, user_id: int) -> bool:
        user = await self.find_user_by_id(user_id)

        if not user:
            return False

        for subscription in user.subscriptions:
            if subscription.is_trial:
                return True

        return False

    async build_data_for_jwt_token() -> Dict:


