from datetime import datetime

from pydantic import BaseModel, EmailStr
from models.user import User


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: EmailStr

class GoogleTokenDto(BaseModel):
    user: User
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    expires_at: datetime
    scope: str
