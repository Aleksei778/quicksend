from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from fastapi_users import schemas


class UserCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    signup_date: Optional[date] = date.today()


class UserRead(schemas.BaseUser[int], BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    signup_date: date

    class Config:
        from_attributes = True
