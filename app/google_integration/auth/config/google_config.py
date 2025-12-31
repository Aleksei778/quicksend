from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_AUTHORIZE_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_SCOPES: list[str] = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v3/userinfo"
    GOOGLE_TOKEN_INFO_URL: str = "https://oauth2.googleapis.com/tokeninfo"
    GOOGLE_JWKS_URL: str = "https://www.googleapis.com/oauth2/v3/certs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

google_settings = GoogleSettings()
