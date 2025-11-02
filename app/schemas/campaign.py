from pydantic import BaseModel
from typing import List
from datetime import datetime


class CampaignCreate(BaseModel):
    sender_name: str
    subject: str
    body_template: str
    recipients: str
    attachment_files: str
    campaign_time: datetime
    recipients: List[str]
    attachments: List[str] = []
    user_id: str


class CampaignRead(BaseModel):
    id: int
    sender_name: str
    subject: str
    body_template: str
    recipients: str
    attachment_files: str
    campaign_time: datetime
    user_id: int

    class Config:
        from_attributes = True


class Attachment:
    name: str
    size: int
    type: str
    content: str


class EmailData(BaseModel):
    recipients: List[str]
    subject: str
    body: str
    attachments: List[Attachment]

    class Config:
        arbitrary_types_allowed = True
