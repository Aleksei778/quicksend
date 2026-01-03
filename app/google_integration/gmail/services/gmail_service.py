import asyncio
from typing import Any, Annotated
from fastapi import HTTPException, status, Depends
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2.credentials import Credentials

from common.db.database import get_db
from google_integration.auth.models.google_token import GoogleToken
from google_integration.auth.services.google_auth_service import (
    GoogleAuthService,
    get_google_auth_service,
)
from google_integration.auth.services.google_token_service import (
    GoogleTokenService,
    get_google_token_service,
)
from google_integration.config.google_config import google_settings
from users.models.user import User


class GoogleGmailService:
    def __init__(
        self,
        db: AsyncSession,
        google_token_service: GoogleTokenService,
        google_auth_service: GoogleAuthService,
    ):
        self._google_token_service = google_token_service
        self._google_auth_service = google_auth_service
        self._db = db

    async def _create_credentials(self, google_token: GoogleToken) -> Credentials:
        return Credentials(
            token=google_token.access_token,
            refresh_token=google_token.refresh_token,
            token_uri=google_settings.GOOGLE_TOKEN_URI,
            client_id=google_settings.GOOGLE_CLIENT_ID,
            client_secret=google_settings.GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )

    async def get_google_gmail_service_for_token(
        self, google_token: GoogleToken
    ) -> Any:
        credentials = await self._create_credentials(google_token)

        return build(
            serviceName="gmail",
            version="v1",
            credentials=credentials,
        )

    async def send_email_via_gmail(
        self,
        user: User,
        raw: str,
    ) -> dict[str, Any]:
        google_token = await self._google_token_service.get_google_token_for_user(user)

        if not google_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google token not found for user {user}",
            )

        if google_token.is_expired:
            await self._google_auth_service.refresh_google_token(google_token)

        gmail_service = await self.get_google_gmail_service_for_token(google_token)

        return await asyncio.to_thread(
            lambda: gmail_service.users()
            .messages()
            .send(
                userId="me",
                body={"raw": raw},
            )
            .execute()
        )


async def get_google_gmail_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    google_token_service: Annotated[
        GoogleTokenService, Depends(get_google_token_service)
    ],
    google_auth_service: Annotated[GoogleAuthService, Depends(get_google_auth_service)],
) -> GoogleGmailService:
    return GoogleGmailService(
        google_token_service=google_token_service,
        google_auth_service=google_auth_service,
        db=db,
    )
