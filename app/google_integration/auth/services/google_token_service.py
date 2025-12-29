from fastapi import Depends
from sqlalchemy.future import select
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from common.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from users.services.user_service import UserService
from users.models.user import User
from google_integration.auth.models.google_token import GoogleToken


class GoogleTokenService:
    def __init__(
        self,
        db: AsyncSession = Depends(AsyncSession),
        user_service: UserService = Depends(UserService),
    ):
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

    async def refresh_google_token(token: TokenOrm, db: AsyncSession):
        if not token or not token.refresh_token:
            raise Exception("Refresh token is missing")

        try:
            print("НЕТ ОШИБКИ ПЕРВЫЙ  1")
            # Make the request to Google OAuth
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://accounts.google.com/o/oauth2/token",
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": token.refresh_token,
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                    },
                )
                response.raise_for_status()  # Raise exception for bad status codes
                new_token_data = response.json()

            print("НЕТ ОШИБКИ ВТОРОЙ  2")
            # Update token in database using SQLAlchemy async pattern
            stmt = (
                update(TokenOrm)
                .where(TokenOrm.id == token.id)
                .values(
                    access_token=new_token_data["access_token"],
                    expires_in=new_token_data["expires_in"],
                    expires_at=datetime.now()
                               + timedelta(seconds=new_token_data["expires_in"]),
                )
            )
            await db.execute(stmt)
            await db.commit()
            return new_token_data["access_token"]

        except httpx.HTTPError as e:
            await db.rollback()

            raise Exception(f"Failed to refresh token: {str(e)}")
        except Exception as e:
            await db.rollback()

            raise Exception(f"Unexpected error while refreshing token: {str(e)}")
