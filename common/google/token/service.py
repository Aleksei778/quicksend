import asyncio
from typing import Annotated
from fastapi import Depends
from google.auth.transport.requests import Request as GoogleRequest
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.database import get_db
from common.google.token.model import GoogleToken
from common.google.token.schema import FindOrCreateGoogleToken
from common.google.token.credentials import create_credentials
from common.users.model import User


class GoogleTokenService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def find_google_token_by_user(self, user: User) -> GoogleToken | None:
        result = await self._db.execute(
            select(GoogleToken)
            .where(GoogleToken.user_id == user.id)
        )

        return result.scalar_one_or_none()

    async def find_or_create_google_token(
        self, find_or_create_google_token_dto: FindOrCreateGoogleToken
    ) -> GoogleToken:
        token = await self.find_google_token_by_user(find_or_create_google_token_dto.user)

        if token is None:
            token = GoogleToken()

        token.user_id = find_or_create_google_token_dto.user.id
        token.access = find_or_create_google_token_dto.access
        token.refresh = find_or_create_google_token_dto.refresh
        token.expiry = find_or_create_google_token_dto.expiry

        self._db.add(token)
        await self._db.commit()
        await self._db.refresh(token)

        return token

    async def refresh_google_token(self, google_token: GoogleToken) -> None:
        if not google_token or not google_token.refresh:
            raise Exception(
                "google_token_service:refresh_google_token: Google refresh token is missing"
            )

        try:
            credentials = await create_credentials(
                google_token=google_token,
                scopes=None,
            )

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, credentials.refresh, GoogleRequest())

            google_token.access = credentials.token
            google_token.expiry = credentials.expiry

            await self._db.commit()
            await self._db.refresh(google_token)

        except Exception as e:
            await self._db.rollback()

            raise Exception(
                f"google_token_service:refresh_google_token: Failed to refresh token: {str(e)}"
            )


async def get_google_token_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GoogleTokenService:
    return GoogleTokenService(db=db)
