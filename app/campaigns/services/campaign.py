import base64
from email.header import Header
from email.mime import multipart, text, image
from email.utils import make_msgid
from typing import Annotated
import pytz
from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import date, datetime, timedelta

from app.campaigns.models.campaign import Campaign
from app.campaigns.config import campaign_config
from app.campaigns.schema import CreateMessage
from app.utils.redis_ import get_redis_client
from campaigns.enum_ import CampaignStatus
from campaigns.services.attachment import AttachmentService, get_attachment_service
from common.utils.database import get_db
from common.users.model import User


class CampaignService:
    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis,
        attachment_service: AttachmentService,
    ) -> None:
        self._redis_client = redis_client
        self._db = db
        self._attachment_service = attachment_service

    async def create_campaign_for_user(
        self, user: User, sender_name: str, subject: str, body_template: str
    ) -> Campaign:
        campaign = Campaign(
            sender_name=sender_name,
            subject=subject,
            body_template=body_template,
            user_id=user.id,
        )

        self._db.add(campaign)
        await self._db.commit()
        await self._db.refresh(campaign)

        return campaign

    async def set_started_at_and_timezone_for_campaign(
        self,
        campaign: Campaign,
        started_at: datetime,
        timezone: str
    ) -> None:
        campaign.started_at = started_at
        campaign.timezone = timezone

        await self._db.commit()
        await self._db.refresh(campaign)

    async def create_message_with_attachment(self, message: CreateMessage) -> str:
        msg = multipart.MIMEMultipart()
        msg["From"] = f"{message.sender_name} <{message.sender_email}>"
        msg["To"] = message.recipient
        msg["Subject"] = Header(f"{message.subject}", "utf-8")
        msg["Message-ID"] = make_msgid()

        msg.attach(text.MIMEText(message.body, "html"))

        total_size = 0

        if message.inline_images:
            for img_id, img_path in message.inline_images:
                with open(img_path, "rb") as img:
                    img_data = img.read()
                    total_size += len(img_data)

                    if total_size > campaign_config.IMAGE_MAX_SIZE:
                        continue

                    img_part = image.MIMEImage(img_data)

                    img_part.add_header("Content-ID", f"<{img_id}>")
                    img_part.add_header("Content-Disposition", "inline")

                    msg.attach(img_part)

        if message.attachments:
            for attachment in message.attachments:
                part = await self._attachment_service.create_mime_part_from_attachment(attachment)

                msg.attach(part)

        return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    async def set_campaign_status(
        self,
        campaign: Campaign,
        campaign_status: CampaignStatus
    ) -> None:
        campaign.status = campaign_status

        await self._db.commit()
        await self._db.refresh(campaign)

    async def process_time_for_campaign_time(
        self,
        campaign_date: str,
        campaign_time: str,
        campaign_timezone: str
    ) -> tuple[datetime, str]:
        naive_datetime = datetime.strptime(
            f"{campaign_date} {campaign_time}", "%Y-%m-%dT%H:%M:%S"
        )

        scheduled_datetime_local = pytz.timezone(campaign_timezone).localize(naive_datetime)

        scheduled_datetime_utc = scheduled_datetime_local.astimezone(pytz.utc)

        now_utc = datetime.now(pytz.utc)
        min_delay = now_utc + timedelta(minutes=5)

        if min_delay > scheduled_datetime_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The time {campaign_date} is in the past",
            )

        return scheduled_datetime_utc, campaign_timezone

    async def get_user_daily_sent_count(self, user: User) -> int:
        key = f"sent:{user.id}:{date.today()}"
        count = await self._redis_client.get(key)

        return int(count) if count else 0

    async def increment_user_sent_count(self, user: User) -> int:
        key = f"sent:{user.id}:{date.today()}"
        new_count = await self._redis_client.incrby(key)

        if new_count == 1:
            await self._redis_client.expire(key, timedelta(days=1))

        return new_count

    async def eager_get_campaign_for_sending(self, campaign_id: int) -> Campaign | None:
        stmt = (
            select(Campaign)
            .options(
                selectinload(Campaign.user),
                selectinload(Campaign.recipients),
                selectinload(Campaign.attachments),
            )
            .where(Campaign.id == campaign_id)
        )
        result = await self._db.execute(stmt)

        return result.scalar_one_or_none()


async def get_campaign_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    attachment_service: Annotated[AttachmentService, Depends(get_attachment_service)],
) -> CampaignService:
    return CampaignService(
        db=db,
        redis_client=redis_client,
        attachment_service=attachment_service
    )
