import base64
from email.encoders import encode_base64
from email.header import Header
from email.mime import multipart, text, image, base
from email.utils import make_msgid
from typing import Annotated
import pytz
from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta

from campaigns.models.campaign import Campaign
from campaigns.config.campaign_config import campaign_settings
from campaigns.schemas.create_message import CreateMessage
from common.db.database import get_db
from common.redis.redis_client import get_redis_client
from users.models.user import User


class CampaignService:
    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis,
    ) -> None:
        self._redis_client = redis_client
        self._db = db

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

    async def create_message_with_attachment(self, message: CreateMessage) -> str:
        msg = multipart.MIMEMultipart()
        msg["From"] = f"{message.sender_name} <{message.sender_email}>"
        msg["To"] = message.recipient
        msg["Subject"] = Header(f"{message.subject}", "utf-8")
        msg["Message-ID"] = make_msgid()

        msg.attach(text.MIMEText(message.body, "html"))

        total_size = 0

        for img_id, img_path in message.inline_images:
            with open(img_path, "rb") as img:
                img_data = img.read()
                total_size += len(img_data)

                if total_size > campaign_settings.IMAGE_MAX_SIZE:
                    continue

                img_part = image.MIMEImage(img_data)

                img_part.add_header("Content-ID", f"<{img_id}>")
                img_part.add_header("Content-Disposition", "inline")

                msg.attach(img_part)

        for attachment in message.attachments:
            part = base.MIMEBase("application", "octet-stream")

            part.set_payload(base64.urlsafe_b64decode(attachment["data"]))
            encode_base64(part)

            if attachment.get("encoded_filename"):
                disposition_str = (
                    f"attachment; filename*=UTF-8''{attachment['encoded_filename']}"
                )
                part.add_header("Content-Disposition", disposition_str)
            else:
                part.add_header(
                    "Content-Disposition", "attachment", filename=attachment["filename"]
                )

            msg.attach(part)

        return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    async def process_time_for_campaign_time(
        self, campaign_date: str, campaign_time: str, user_timezone_str: str | None
    ) -> datetime:
        naive_datetime = datetime.strptime(
            f"{campaign_date} {campaign_time}", "%Y-%m-%dT%H:%M:%S"
        )

        if user_timezone_str is None:
            user_timezone_str = "UTC"

        user_timezone = pytz.timezone(user_timezone_str)

        scheduled_datetime_local = user_timezone.localize(naive_datetime)

        scheduled_datetime_utc = scheduled_datetime_local.astimezone(pytz.utc)

        now_utc = datetime.now(pytz.utc)
        min_delay = now_utc + timedelta(hours=1)

        if min_delay > scheduled_datetime_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The time {campaign_date} is in the past",
            )

        return scheduled_datetime_utc

    async def get_user_daily_sent_count(self, user: User) -> int:
        key = f"sent:{user.id}:{date.today()}"
        count = await self._redis_client.get(key)

        return int(count) if count else 0

    async def increment_user_sent_count(self, user: User) -> int:
        key = f"sent:{user.id}:{date.today()}"
        new_count = await self._redis_client.incr(key)

        if new_count == 1:
            await self._redis_client.expire(key, timedelta(days=1))

        return new_count


async def get_campaign_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> CampaignService:
    return CampaignService(
        db=db,
        redis_client=redis_client,
    )
