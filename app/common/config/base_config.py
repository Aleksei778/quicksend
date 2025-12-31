from pydantic_settings import (
    BaseSettings as BasePydanticSettings,
    SettingsConfigDict
)


class BaseSettings(BasePydanticSettings):
    BACKEND_URL: str = ""
    FRONTEND_URL: str = ""
    CHROME_EXTENSION_URL: str = ""
    DB_PORT: int = 5432
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_PASSWORD: str = ""
    DB_USER: str = ""
    ENCRYPTION_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

base_settings = BaseSettings()
