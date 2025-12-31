from fastapi import Depends
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from google_integration.auth.models.google_token import GoogleToken
from google_integration.auth.schemas.find_or_create_google_token import FindOrCreateGoogleToken

from common.db.database import get_db


class GoogleTokenService:
    def __init__(self, db: AsyncSession = Depends(get_db)) -> None:
        self.db = db

    async def get_google_token_for_user(self, user_id: int) -> GoogleToken | None:
        result = await self.db.execute(
            select(GoogleToken).where(GoogleToken.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_or_create_google_token(
            self,
            find_or_create_google_token_dto: FindOrCreateGoogleToken
    ) -> GoogleToken:
        user_id = find_or_create_google_token_dto.user.id
        token = await self.find_token_by_user_id(user_id)

        if token is None:
            token = GoogleToken()

        token.user_id = user_id
        token.access_token = find_or_create_google_token_dto.access_token
        token.refresh_token = find_or_create_google_token_dto.refresh_token
        token.expires_in = find_or_create_google_token_dto.expires_in
        token.expires_at = find_or_create_google_token_dto.expires_at
        token.scope = find_or_create_google_token_dto.scope
        token.token_type = find_or_create_google_token_dto.token_type

        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)

        return token

    async def find_token_by_user_id(self, user_id: int) -> GoogleToken | None:
        result = await self.db.execute(
            select(GoogleToken).where(GoogleToken.user_id == user_id)
        )
        return result.scalar_one_or_none()
