from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from users.models.user import User


class FindOrCreateGoogleToken(BaseModel):
    user: User
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
