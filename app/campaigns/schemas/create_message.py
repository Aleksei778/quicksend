from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from campaigns.models.attachment import Attachment


class CreateMessage(BaseModel):
    sender_email: EmailStr
    recipient: str
    subject: str
    body: str
    sender_name: str
    attachments: Optional[list[Attachment]] = None
    inline_images: Optional[list[str]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
