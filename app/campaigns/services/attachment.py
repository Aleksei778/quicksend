import base64
import mimetypes
from email import encoders
from email.mime import base
from typing import Any, Annotated
from urllib.parse import quote
from fastapi import UploadFile, Depends
from sqlalchemy import func, Date, cast
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.campaigns.models.campaign import Campaign
from app.campaigns.models.attachment import Attachment
from common.utils.database import get_db
from common.users.model import User


class AttachmentService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def prepare_attachment_for_gmail(self, file: UploadFile) -> dict[str, Any]:
        content = b""
        while chunk := await file.read(8192):
            content += chunk

        filename = file.filename or "unnamed"

        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype is None:
            mimetype = "application/octet-stream"

        return {
            "filename": filename,
            "mimetype": mimetype,
            "size": len(content),
            "content": base64.urlsafe_b64encode(content).decode("utf-8"),
        }

    async def create_mime_part_from_attachment(self, attachment: Attachment) -> base.MIMEBase:
        main_type, sub_type = attachment.mimetype.split("/", 1)

        mimepart = base.MIMEBase(main_type, sub_type)
        mimepart.set_payload(attachment.content)
        encoders.encode_base64(mimepart)

        encoded_filename = quote(attachment.filename)

        mimepart.add_header(
            _name="Content-Disposition",
            _value=f'attachment; filename="{encoded_filename}"',
        )
        mimepart.add_header("Content-ID", f"<{attachment.filename}>")

        return mimepart

    async def create_attachment(
        self,
        campaign: Campaign,
        filename: str,
        size: int,
        mimetype: str,
        content: str,
    ) -> Attachment:
        attachment = Attachment(
            campaign_id=campaign.id,
            filename=filename,
            size=size,
            mimetype=mimetype,
            content=content,
        )

        self._db.add(attachment)
        await self._db.commit()
        await self._db.refresh(attachment)

        return attachment


async def get_attachment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttachmentService:
    return AttachmentService(db=db)
