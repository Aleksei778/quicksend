from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from datetime import datetime

from app.common.db.database import Base
from app.campaigns.enum.campaign_status import CampaignStatus


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    body_template = Column(Text, nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_at = Column(DateTime, nullable=True)
    timezone = Column(String, nullable=False, default="UTC")

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="campaigns")
    recipients = relationship("Recipient", back_populates="campaign")
    attachments = relationship("Attachment", back_populates="campaign")
