from email import encoders
from email.mime import base
from typing import Any, Annotated
from urllib.parse import quote
from fastapi import Depends
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models.attachment import Attachment
from common.utils.database import get_db


class AttachmentService:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def bulk_create_attachments(
        self,
        campaign_id: int,
        files_data: list[dict[str, Any]],
    ) -> None:
        final_files_data = [
            {
                "campaign_id": campaign_id,
                **file
            }
            for file in files_data
        ]
        stmt = (insert(Attachment)
                .values(final_files_data)
                .returning(Attachment))

        await self._db.execute(stmt)
        await self._db.commit()

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


async def get_attachment_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AttachmentService:
    return AttachmentService(db=db)
