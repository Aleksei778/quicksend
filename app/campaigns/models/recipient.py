from sqlalchemy import Uuid, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType
from datetime import datetime

from common.database import Base


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Uuid, primary_key=True, autoincrement=True)
    email = Column(EmailType, nullable=False)
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    opened_at = Column(DateTime, nullable=True)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    campaign = relationship(argument="Campaign", back_populates="recipients")
