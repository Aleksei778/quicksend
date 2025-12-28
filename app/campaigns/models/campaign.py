from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Enum,
    Uuid
)
from datetime import datetime

from common.database import Base
from enums.campaing_status import CampaignStatus


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Uuid, primary_key=True, index=True, autoincrement=True)
    sender_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    body_template = Column(Text, nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_at = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="campaigns")
    recipients = relationship("Recipient", back_populates="campaigns")
    attachments = relationship("Attachment", back_populates="campaign")
