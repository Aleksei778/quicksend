from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    Text,
    DateTime,
)

from common.utils.database import Base
from common.utils.security import decrypt, encrypt


class GoogleToken(Base):
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    _access = Column("access", Text, index=True, nullable=False)
    _refresh = Column("refresh", Text, index=True, nullable=False)
    expiry = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="google_token")

    @property
    def access(self) -> str:
        return decrypt(self._access)

    @property
    def refresh(self) -> str:
        return decrypt(self._refresh)

    @access.setter
    def access(self, value: str) -> None:
        self._access= encrypt(value)

    @refresh.setter
    def refresh(self, value: str) -> None:
        self._refresh = encrypt(value)

    @property
    def is_expired(self) -> bool:
        return bool(datetime.now() > self.expiry)
