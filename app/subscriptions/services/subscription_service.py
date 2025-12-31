from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from users.models.user import User
from subscriptions.models.subscription import Subscription
from subscriptions.enum.plan import SubscriptionPlan
from campaigns.services.campaign_service import CampaignService


class SubscriptionService:
    def __init__(self, db: AsyncSession, campaign_service: CampaignService):
        self.db = db
        self.campaign_service = campaign_service

    async def is_user_already_used_trial(self, user: User) -> bool:
        for subscription in user.subscriptions:
            if subscription.is_trial:
                return True

        return False

    async def get_subscription_info_for_jwt(self, user: User) -> dict[str, str]:
        active_sub = await self.get_user_active_sub(user)
        subscription_info = {"plan": "No active subscription"}

        if active_sub:
            subscription_info["plan"] = active_sub.plan

        return subscription_info

    async def get_user_subs(self, user: User) -> list[Subscription] | None:
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
    ) -> tuple[bool, str]:
            subscription = await self.get_user_active_sub(user)
            if not subscription:
                return False, "No active subscription"

            active_sub_plan = subscription.plan
            today = date.today()
            previous_recipients_count = await self.campaign_service.get_recipients_count_by_date_for_user(user, today)
            total_recipients = previous_recipients_count + current_recipients_count

            restrict_condition = (
                total_recipients > 50 and active_sub_plan == SubscriptionPlan.TRIAL
            ) or (
                total_recipients > 500 and active_sub_plan == SubscriptionPlan.STANDARD
            )

            if restrict_condition:
                return False, "Already used limits"

            return True
