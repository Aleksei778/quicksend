from sqlalchemy import (
    Column,
    Type,
    Integer,
    Enum,
    Boolean,
    DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan = Column(Enum())
    is_active = Column(Boolean)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ends_at = Column(DateTime, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="subscription")
