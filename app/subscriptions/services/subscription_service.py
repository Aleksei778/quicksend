from datetime import datetime
from typing import Annotated
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.database import get_db
from common.redis.redis_client import get_redis_client
from payments.models.payment import Payment
from subscriptions.enum.plan import SubscriptionPlan
from users.models.user import User
from subscriptions.models.subscription import Subscription
from campaigns.services.campaign_service import CampaignService, get_campaign_service


class SubscriptionService:
    def __init__(
        self,
        db: AsyncSession,
        campaign_service: CampaignService,
        redis_client: Redis,
    ) -> None:
        self._db = db
        self._campaign_service = campaign_service
        self._redis_client = redis_client

    async def is_user_already_used_trial(self, user: User) -> bool:
        result = await self._db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.plan == SubscriptionPlan.TRIAL)
        )

        trial_sub = result.scalar_one_or_none()

        if trial_sub is None:
            return False

        return True

    async def set_last_payment_for_subscription(
        self, subscription: Subscription, last_payment: Payment
    ) -> None:
        subscription.last_payment = last_payment

        await self._db.commit()

    async def create_subscription(
        self,
        user: User,
        plan: SubscriptionPlan,
        end_at: datetime,
    ) -> Subscription:
        subscription = Subscription(
            user_id=user.id,
            plan=plan,
            end_at=end_at,
        )

        self._db.add(subscription)
        await self._db.commit()
        await self._db.refresh(subscription)

        return subscription

    async def get_user_active_subscription(self, user: User) -> Subscription | None:
        result = await self._db.execute(
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.is_active == True)
        )

        return result.scalar_one_or_none()

    async def check_if_user_can_send_emails(self, user: User) -> tuple[bool, str]:
        subscription = await self.get_user_active_subscription(user)
        if not subscription:
            return False, "No active subscription"

        today_recipients_count = await self._campaign_service.get_user_daily_sent_count(
            user
        )

        if today_recipients_count > subscription.plan.get_recipients_limit():
            return False, "Already used limits"

        return True, ""


async def get_subscription_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    campaign_service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> SubscriptionService:
    return SubscriptionService(
        db=db,
        redis_client=redis_client,
        campaign_service=campaign_service,
    )
