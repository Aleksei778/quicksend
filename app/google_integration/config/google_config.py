from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.config.base_config import base_settings


class GoogleSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    WEBSITE_GOOGLE_SCOPES: list[str] = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    EXTENSION_GOOGLE_SCOPES: list[str] = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/spreadsheets.readonly'
    ]
    GOOGLE_TOKEN_URI: str = "https://accounts.google.com/o/oauth2/token"
    GOOGLE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    REDIRECT_URI: str = f"{base_settings.BACKEND_URL}/api/auth/google/callback"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


google_settings = GoogleSettings()
