from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    Date,
    TIMESTAMP,
    Boolean,
    Numeric,
)
from sqlalchemy_utils import EmailType
from datetime import date, datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(EmailType, unique=True, nullable=False, index=True)
    signup_date = Column(Date, nullable=False, default=date.today)
    picture = Column(String, nullable=True)

    campaigns = relationship("Campaign", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")

    token = relationship("Token", back_populates="user", uselist=False)


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_name = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    body_template = Column(Text, nullable=True)
    recipients = Column(Text, nullable=True)
    attachment_files = Column(Text, nullable=True)
    campaign_time = Column(DateTime, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="campaigns")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan = Column(String)  # "free_trial", "basic", "premium"
    status = Column(String)  # "active", "inactive", "not paid"
    start_date = Column(Date, nullable=False, default=datetime.utcnow)
    end_date = Column(Date, nullable=False)
    is_trial = Column(Boolean, default=False)

    provider = Column(String)  # "paypal", "yookassa"
    provider_sub_id = Column(String, unique=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    currency = Column(String)
    amount = Column(Numeric(10, 2))
    status = Column(String)  # "pending", "successfull", "failed"
    payment_method = Column(String)
    transaction_id = Column(String, unique=True)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    subscription = relationship("Subscription", back_populates="payments")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    access_token = Column(String, index=True, nullable=False)
    refresh_token = Column(String, index=True, nullable=True)
    token_type = Column(String, nullable=False)
    expires_in = Column(Integer, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    scope = Column(String, nullable=False)

    user = relationship("User", back_populates="token")
