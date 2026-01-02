import base64
import mimetypes
from email import encoders
from email.mime import base
from typing import Any
from urllib.parse import quote

from fastapi import UploadFile
from sqlalchemy import func, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from campaigns.models.attachment import Attachment
from campaigns.models.campaign import Campaign
from users.models.user import User


class AttachmentService:
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

    async def prepare_attachment_for_gmail(self, file: UploadFile) -> dict[str, Any]:
        content = b""
        while chunk := await file.read(8192):
            content += chunk

        filename = file.filename or "unnamed"
        encoded_filename = quote(filename)

        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype is None:
            mimetype = 'application/octet-stream'

        main_type, sub_type = mimetype.split('/', 1)

        mimepart = base.MIMEBase(main_type, sub_type)
        mimepart.set_payload(content)
        encoders.encode_base64(mimepart)

        mimepart.add_header(
            _name='Content-Disposition',
            _value=f'attachment; filename="{encoded_filename}"',
        )
        mimepart.add_header("Content-ID", f"<{filename}>")

        return {
            "filename": encoded_filename,
            "content": content,
            "mimetype": mimetype,
            "size": len(content),
            "mime_part": mimepart,
            "encoded_content": base64.urlsafe_b64encode(content).decode("utf-8"),
        }

    async def create_attachment(
        self,
        name: str,
        size: int,
        mimetype: str
    ) -> Attachment:
        attachment = Attachment(
            name=name,
            size=size,
            mimetype=mimetype,
        )

        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)

        return attachment
