from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime

from common.utils.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    mimetype = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    campaign = relationship(argument="Campaign", back_populates="attachments")
