from typing import Optional, List
from pydantic import BaseModel

from campaigns.models.attachment import Attachment


class CreateMessage(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str
    sender_name: str
    attachments: Optional[List[Attachment]] = None
    inline_images: Optional[List[str]] = None
