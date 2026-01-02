from typing import Annotated
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import func, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from campaigns.models.campaign import Campaign
from campaigns.models.recipient import Recipient
from common.db.database import get_db
from users.models.user import User


class RecipientService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]):
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

    async def create_recipient(
        self,
        campaign: Campaign,
        email: EmailStr,
    ) -> Recipient:
        recipient = Recipient(
            email=email,
            campaign_id=campaign.id,
        )

        self.db.add(recipient)
        await self.db.commit()
        await self.db.refresh(recipient)

        return recipient
