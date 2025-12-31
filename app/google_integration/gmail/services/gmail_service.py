from fastapi.params import Depends
from googleapiclient.discovery import build, Resource
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2.credentials import Credentials

from common.db.database import get_db
from google_integration.auth.models.google_token import GoogleToken
from common.config.base_config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


class GoogleGmailService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
    ):
        self.db = db

    async def _create_credentials(self, google_token: GoogleToken):
        return Credentials(
            token=google_token.access_token,
            refresh_token=google_token.refresh_token,
            token_uri="https://accounts.google.com/o/oauth2/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )

    async def get_google_gmail_service_for_token(self, google_token: GoogleToken) -> Resource:
        credentials = await self._create_credentials(google_token)

        return build(
            serviceName="gmail",
            version="v1",
            credentials=credentials,
        )
