from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy_utils import EmailType
from datetime import datetime

from common.utils.logger import logger
from common.utils.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(EmailType, unique=True, nullable=False, index=True)
    oauth_id = Column(String(255), nullable=True, index=True)
    picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    google_token = relationship(argument="GoogleToken", back_populates="user")

def add_relationships_for_app():
    from sqlalchemy.orm import relationship

    if not hasattr(User, 'campaigns'):
        User.campaigns = relationship("Campaign", back_populates="user")

    if not hasattr(User, 'subscriptions'):
        User.subscriptions = relationship("Subscription", back_populates="user")

    if not hasattr(User, 'payments'):
        User.payments = relationship(argument="Payment", back_populates="user")

    logger.info("Adding relationships for app")
