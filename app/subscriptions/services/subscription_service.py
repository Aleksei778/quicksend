from datetime import datetime, UTC, timedelta
from typing import Annotated
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.database import get_db
from app.common.redis.redis_client import get_redis_client
from app.subscriptions.enum.plan import SubscriptionPlan
from app.users.models.user import User
from app.subscriptions.models.subscription import Subscription
from app.campaigns.services.campaign_service import CampaignService, get_campaign_service


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

        return bool(result.scalar_one_or_none())

    async def create_trial(self, user: User) -> None:
        if await self.is_user_already_used_trial(user=user):
            return

        now = datetime.now(UTC)

        started_at = now
        end_at = now + timedelta(days=SubscriptionPlan.TRIAL.get_days_count())

        await self.create_subscription(
            user=user,
            plan=SubscriptionPlan.TRIAL,
            started_at=started_at,
            end_at=end_at,
        )

    async def create_subscription(
        self,
        user: User,
        plan: SubscriptionPlan,
        started_at: datetime,
        end_at: datetime,
    ) -> Subscription:
        subscription = Subscription(
            user_id=user.id,
            plan=plan,
            started_at=started_at,
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
