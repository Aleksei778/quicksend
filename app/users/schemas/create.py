from typing import Optional
from pydantic import EmailStr, BaseModel


class Create(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    oauth_id: Optional[str] = None
    timezone: Optional[str] = None
