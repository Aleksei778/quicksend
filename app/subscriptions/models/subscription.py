from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import Column, Integer, Enum, Boolean, DateTime, ForeignKey

from common.db.database import Base
from subscriptions.enum.plan import SubscriptionPlan


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan = Column(Enum(SubscriptionPlan))
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_at = Column(DateTime, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    failed_payment_attempts = Column(Integer, default=0)
    last_payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship(argument="User", back_populates="subscriptions")
    last_payment = relationship(
        argument="Payment", foreign_keys="subscriptions.last_payment_id"
    )
    payments = relationship(argument="Payment", back_populates="subscription")
