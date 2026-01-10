from google.oauth2.credentials import Credentials

from common.google.token.model import GoogleToken
from common.google.config import google_settings


async def create_credentials(
    google_token: GoogleToken,
    scopes: list[str] | None,
) -> Credentials:
    return Credentials(
        token=google_token.access,
        refresh_token=google_token.refresh,
        token_uri=google_settings.GOOGLE_TOKEN_URI,
        client_id=google_settings.GOOGLE_CLIENT_ID,
        client_secret=google_settings.GOOGLE_CLIENT_SECRET,
        scopes=scopes,
    )
