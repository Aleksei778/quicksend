from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from database.models import User, Subscription
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

    async def find_user_by_email(self, email: str) -> User:
        return self.db.get(User, email)

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

    async def can_user_send_emails(self, user_id: int, recipients_count: int) -> Tuple[bool, str]:
        subs = await self.get_user_subs(user_id)

        if not subs:
            return False, "No subs"

        subscription = await self.get_active_sub(user.id)
        print(subscription)
        print("нет ошибки2")
        if not subscription:
            return False, "No active sub"

        active_sub_plan = subscription.plan
        print("нет ошибки3")
        today = date.today()

        prev_recipients_count = await self.get_all_recipients_in_campaigns_by_date(user.id, today)
        print("нет ошибки4")
        print(prev_recipients_count + cur_recipients_count > and )

        if (prev_recipients_count + cur_recipients_count > 50 and active_sub_plan == "free_trial"):
            return False, "Recipient limit per day exceeded in trial plan"

        if (prev_recipients_count + cur_recipients_count > 500 and active_sub_plan == "standart"):
            return False, "Recipient limit per day exceeded in standart plan"

        return True, "Active sub"
