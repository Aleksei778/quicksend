from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from app.campaigns.models.attachment import Attachment


class CreateMessage(BaseModel):
    sender_email: EmailStr
    recipient: str
    subject: str
    body: str
    sender_name: str
    attachments: Optional[list[Attachment]] = None
    inline_images: Optional[list[str]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

class AttachmentData(BaseModel):
    filename: str
    content: str
    mimetype: Optional[str] = "application/octet-stream"
    size: Optional[int] = 0

    def to_dict(self) -> dict:
        return self.model_dump()

class CampaignRequest(BaseModel):
    subject: str
    body: str
    recipients: list[EmailStr]
    files: Optional[list[AttachmentData]] = []
    date: Optional[str] = None
    time: Optional[str] = None
    timezone: Optional[str] = None

    def need_to_schedule(self) -> bool:
        return all([self.date, self.time, self.timezone])
