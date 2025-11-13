from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.google_token import GoogleToken


class GoogleTokenService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_google_token_for_user(self, user_id: int) -> GoogleToken:
        result = await self.db.execute(
            select(GoogleToken).where(GoogleToken.user_id == user_id)
        )

        return result.scalar_one_or_none()

