from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Enum,
    JSON,
    DateTime,
    DECIMAL
)
from sqlalchemy.orm import relationship

from common.database.base import Base
from payments.enum.provider import PaymentProvider as PaymentProviderEnum
from payments.enum.payment_status import PaymentStatus as PaymentStatusEnum
from payments.enum.currency import Currency as CurrencyEnum


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    external_payment_id = Column(String(100), unique=True, nullable=False, index=True)
    provider = Column(Enum(PaymentProviderEnum), default=PaymentStatusEnum.PENDING)

    amount = Column(DECIMAL, nullable=False)
    currency = Column(Enum(CurrencyEnum), default=CurrencyEnum.RUB)
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)
    payment_method = Column(String(50), nullable=True)
    description = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

    metadata = Column(JSON, nullable=True)

    user = relationship("User", back_populates="payments")
