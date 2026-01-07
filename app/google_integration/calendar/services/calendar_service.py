from typing import Any
import pytz
from googleapiclient.discovery import build

from common.log.logger import logger
from google_integration.auth.models.google_token import GoogleToken
from google_integration.auth.utils.credentials import create_credentials


class GoogleCalendarService:
    async def get_google_calendar_service(self, google_token: GoogleToken) -> Any:
        credentials = await create_credentials(
            google_token=google_token,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )

        return build(
            serviceName="calendar",
            version="v3",
            credentials=credentials,
        )

    async def get_user_timezone(
        self, google_token: GoogleToken
    ) -> pytz.tzinfo.BaseTzInfo:
        try:
            service = await self.get_google_calendar_service(google_token)

            settings = service.settings().get(setting="timezone").execute()
            timezone = settings.get("value")
            if timezone:
                return pytz.timezone(timezone)

            calendar = service.calendars().get(calendarId="primary").execute()
            timezone = calendar.get("timeZone")
            if timezone:
                return pytz.timezone(timezone)

        except Exception as e:
            logger.info(f"Failed to get user timezone: {e}")

        return pytz.utc


async def get_google_calendar_service() -> GoogleCalendarService:
    return GoogleCalendarService()
