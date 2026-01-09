from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.users.models.user import User


class FindOrCreateGoogleToken(BaseModel):
    user: User
    access: str
    refresh: str
    expiry: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)
