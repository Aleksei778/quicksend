from fastapi.params import Depends
from googleapiclient.discovery import build, Resource
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2.credentials import Credentials
import asyncio

from models.google_token import GoogleToken
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from services.google_token_service import GoogleTokenService


class SendEmailsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_google_gmail_service_for_token(self, google_token: GoogleToken) -> Resource:
        creds = Credentials(
            token=google_token.access_token,
            refresh_token=google_token.refresh_token,
            token_uri="https://accounts.google.com/o/oauth2/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )

        return build("gmail", "v1", credentials=creds)

    async def send_emails_via_gmail_api(self, google_token_service: GoogleTokenService = Depends(GoogleTokenService)):
        try:
            stmt_user = select(UserOrm).where(UserOrm.email == user_id)
            result_user = await db.execute(stmt_user)
            user = result_user.scalar_one_or_none()

            if not user:
                logger.error(f"UserOrm with ID {user_id} not found")
                return

            gmail_service = await get_gmail_service(user, db)

            response = await asyncio.to_thread(
                lambda: gmail_service.users()
                .messages()
                .send(userId="me", body=message_data["message"])
                .execute()
            )
            logger.info(f"Email to {message_data['recipient']} sent successfully")
        except HttpError as e:
            logger.error(f"Failed to send email to {message_data['recipient']}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error for {message_data['recipient']}: {e}")