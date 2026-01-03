from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_utils import EmailType
from datetime import datetime

from common.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(EmailType, unique=True, nullable=False, index=True)
    oauth_id = Column(String(255), nullable=True, index=True)
    picture = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    campaigns = relationship(argument="Campaign", back_populates="user")
    subscriptions = relationship(argument="Subscription", back_populates="user")
    google_token = relationship(argument="GoogleToken", back_populates="user")
