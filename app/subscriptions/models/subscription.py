from sqlalchemy import (
    Column,
    Integer,
    Enum,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from common.database.base import Base
from subscriptions.enum.plan import SubscriptionPlan


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan = Column(Enum(SubscriptionPlan))
    is_active = Column(Boolean)
    auto_renew = Column(Boolean, default=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_at = Column(DateTime, nullable=False)
    canceled_at = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="subscriptions")
