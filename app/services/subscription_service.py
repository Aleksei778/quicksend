from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Tuple

from models.user import User
from models.subscription import Subscription
from enums.cant_send_emails_reasons import CantSendEmailsReasons
from enums.subscriptions_plans import SubscriptionPlans
from services.campaign_service import CampaignService


class SubscriptionService:
    def __init__(self, db: AsyncSession, campaign_service: CampaignService):
        self.db = db
        self.campaign_service = campaign_service

    async def is_user_already_used_trial(self, user: User) -> bool:
        for subscription in user.subscriptions:
            if subscription.is_trial:
                return True

        return False

    async def get_user_subs(self, user: User) -> List[Subscription] | None:
        return user.subscriptions

    async def get_user_active_sub(self, user: User) -> Subscription | None:
        for subscription in user.subscriptions:
            if subscription.is_active:
                return subscription

        return None

    async def check_if_user_can_send_emails(
            self,
            user: User,
            current_recipients_count: int
    ) -> Tuple[bool, CantSendEmailsReasons]:
            subs = await self.get_user_subs(user)
            if not subs:
                return False, CantSendEmailsReasons.NO_SUBSCRIPTIONS

            subscription = await self.get_user_active_sub(user)
            if not subscription:
                return False, CantSendEmailsReasons.NO_ACTIVE_SUBSCRIPTION

            active_sub_plan = subscription.plan
            today = date.today()
            previous_recipients_count = await self.campaign_service.get_recipients_count_by_date_for_user(user, today)
            total_recipients = previous_recipients_count + current_recipients_count

            restrict_condition = (
                total_recipients > 50 and active_sub_plan == SubscriptionPlans.TRIAL
            ) or (
                total_recipients > 500 and active_sub_plan == SubscriptionPlans.STANDARD
            )

            if restrict_condition:
                return False, CantSendEmailsReasons.LIMIT_EXCEEDED

            return True, CantSendEmailsReasons.CAN_SEND_EMAILS

    async def build_subscription_data_for_jwt(self) -> :