from typing import Any, Annotated
from fastapi.params import Depends
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2.credentials import Credentials

from common.db.database import get_db
from google_integration.auth.models.google_token import GoogleToken
from google_integration.config.google_config import google_settings


class GoogleCalendarService:
    def __init__(self, db: Annotated[AsyncSession, Depends(get_db)]):
        self.db = db

    async def _create_credentials(self, google_token: GoogleToken) -> Credentials:
        return Credentials(
            token=google_token.access_token,
            refresh_token=google_token.refresh_token,
            token_uri=google_settings.GOOGLE_TOKEN_URI,
            client_id=google_settings.GOOGLE_CLIENT_ID,
            client_secret=google_settings.GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )

    async def get_google_calendar_service(self, google_token: GoogleToken) -> Any:
        credentials = await self._create_credentials(google_token)

        return build(
            serviceName="calendar",
            version="v3",
            credentials=credentials,
        )

    async def get_user_timezone(self, google_token: GoogleToken) -> str:
        service = await self.get_google_calendar_service(google_token)

        settings = service.settings().get(setting='timezone').execute()
        timezone = settings.get('value')
        if timezone:
            return timezone

        calendar = service.calendars().get(calendarId='primary').execute()
        timezone = calendar.get('timeZone')
        if timezone:
            return timezone

        return "UTC"
