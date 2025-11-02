from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    DateTime,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from db.base import Base
from core.security import decrypt, encrypt


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    _access_token = Column(Text, index=True, nullable=False)
    _refresh_token = Column(Text, index=True, nullable=False)
    token_type = Column(String, nullable=False)
    expires_in = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    scope = Column(String, nullable=False)

    user = relationship("User", back_populates="google_token")

    @hybrid_property
    def access_token(self):
        return decrypt(self._access_token)

    @hybrid_property
    def refresh_token(self):
        return decrypt(self._refresh_token)

    @access_token.setter
    def access_token(self, value):
        self._access_token = encrypt(value)

    @refresh_token.setter
    def refresh_token(self, value):
        self._refresh_token = encrypt(value)
