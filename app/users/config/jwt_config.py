from pydantic_settings import BaseSettings, SettingsConfigDict


class JwtSettings(BaseSettings):
    JWT_ALGORITHM: str = ""
    JWT_ACCESS_SECRET_FOR_AUTH: str = ""
    JWT_REFRESH_SECRET_FOR_AUTH: str = ""
    JWT_ACCESS_TOKEN_EXPIRATION_HOURS: int = 1
    JWT_REFRESH_TOKEN_EXPIRATION_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


jwt_settings = JwtSettings()
