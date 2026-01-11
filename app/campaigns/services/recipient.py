from typing import Annotated
from fastapi import Depends
from pydantic import EmailStr
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models.campaign import Campaign
from app.campaigns.models.recipient import Recipient
from common.utils.database import get_db


class RecipientService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def bulk_create_recipients(
        self,
        campaign_id: int,
        emails: list[EmailStr],
    ) -> None:
        recipients_data = [
            {
                "campaign_id": campaign_id,
                "email": str(email)
            }
            for email in emails
        ]

        stmt = (insert(Recipient)
                .values(recipients_data)
                .returning(Recipient))

        await self._db.execute(stmt)
        await self._db.commit()


async def get_recipient_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecipientService:
    return RecipientService(db=db)
