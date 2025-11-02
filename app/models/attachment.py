from sqlalchemy import (
    Integer,
    Column,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from db.base import Base


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)
    s3_link = Column(String, nullable=False)

    campaign_id = Column(Integer, ForeignKey("campaigns.id"))

    campaign = relationship("Campaign", back_populates="attachments")
