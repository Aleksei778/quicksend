from sqlalchemy import func, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from campaigns.models.campaign import Campaign
from users.models.user import User


class CampaignService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recipients_count_by_date_for_user(
        self,
        user: User,
        camp_date: date
    ) -> int:
        result = await self.db.execute(
            func.sum(Campaign.recipients)
            .where(Campaign.user_id == user.id)
            .where(cast(Campaign.started_at, Date) == camp_date)
        )

        total_count = result.scalar()

        return total_count or 0
