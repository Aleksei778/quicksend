from pydantic_settings import BaseSettings, SettingsConfigDict


class JwtSettings(BaseSettings):
    JWT_ALGORITHM = ""
    JWT_ACCESS_SECRET_FOR_AUTH = ""
    JWT_REFRESH_SECRET_FOR_AUTH = ""
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = 30
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

jwt_settings = JwtSettings()
