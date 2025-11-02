from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_utils import EmailType
from datetime import datetime

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(EmailType, unique=True, nullable=False, index=True)
    picture = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now())

    campaigns = relationship("Campaign", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    token = relationship("Token", back_populates="user", uselist=False)
