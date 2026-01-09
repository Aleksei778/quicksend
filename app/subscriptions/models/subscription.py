from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, Enum, Boolean, DateTime, ForeignKey

from app.common.db.database import Base
from app.subscriptions.enum.plan import SubscriptionPlan


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan = Column(Enum(SubscriptionPlan))
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    end_at = Column(DateTime(timezone=True), nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    failed_payment_attempts = Column(Integer, default=0)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship(argument="User", back_populates="subscriptions")
    payments = relationship(argument="Payment", back_populates="subscription")
