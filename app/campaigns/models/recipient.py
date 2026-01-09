from sqlalchemy import Column, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType

from app.common.db.database import Base


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(EmailType, nullable=False)
    sent_at = Column(DateTime, nullable=True)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    campaign = relationship(argument="Campaign", back_populates="recipients")
