import base64
from email.encoders import encode_base64
from email.header import Header
from email.mime import multipart, text, image
from email.utils import make_msgid
from sqlalchemy import func, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from campaigns.models.campaign import Campaign
from campaigns.schemas.create_message import CreateMessage
from users.models.user import User
from campaigns.config.campaign_config import campaign_settings


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

    async def create_message_with_attachment(self, message: CreateMessage) -> None:
        msg = multipart.MIMEMultipart()
        msg["From"] = f"{message.sender_name} <{message.sender}>"
        msg["To"] = message.recipient
        msg["Subject"] = Header(f"{message.subject}", "utf-8")
        msg["Message-ID"] = make_msgid()

        msg.attach(text.MIMEText(message.body, "html"))

        total_size = 0

        for img_id, img_path in message.inline_images.items():
            with open(img_path, "rb") as img:
                img_data = img.read()
                total_size += len(img_data)

                if total_size > campaign_settings.IMAGE_MAX_SIZE:
                    continue

                img_part = image.MIMEImage(img_data)

                img_part.add_header("Content-ID", f"<{img_id}>")
                img_part.add_header("Content-Disposition", "inline")

                msg.attach(img_part)

        for attachment in attachments:
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

        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        return {"raw": raw_msg}
