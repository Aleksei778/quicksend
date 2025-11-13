from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from googleapiclient.discovery import build


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_user_already_used_trial(self, user: User) -> bool:
        for subscription in user.subscriptions:
            if subscription.is_trial:
                return True

        return False

    async def get_user_subs(self, user: User) -> List[Subscription] | None:
        return user.subscriptions

    async def check_if_user_can_send_emails(self, user: User) -> Tuple[bool, str]:

