from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Integer,
    Column,
    String,
    DateTime,
    ForeignKey,
)

from common.db.database import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    mimetype = Column(String, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    campaign = relationship(argument="Campaign", back_populates="attachments")
