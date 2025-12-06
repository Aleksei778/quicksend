from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.google_token import GoogleToken
from schemas.token_schema import GoogleTokenDto


class GoogleTokenService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_google_token_for_user(self, user_id: int) -> GoogleToken:
        result = await self.db.execute(
            select(GoogleToken).where(GoogleToken.user_id == user_id)
        )

        return result.scalar_one_or_none()

    async def create_or_update_token(self, update_dto: GoogleTokenDto) -> GoogleToken:
        token = await self.find_token_by_user_id(update_dto.user_id)

        if token is None:
            token = GoogleToken()

        token.access_token = update_dto.access_token
        token.refresh_token = update_dto.refresh_token
        token.expires_in = update_dto.expires_in
        token.expires_at = update_dto.expires_at
        token.scope = update_dto.scope

        self.db.add(token)
        await self.db.flush()
        await self.db.commit()

        return token

    async def find_token_by_user_id(self, user_id) -> GoogleToken | None:
        return await self.db.get(GoogleToken, user_id == user_id)
