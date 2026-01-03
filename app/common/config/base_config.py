from pydantic_settings import BaseSettings as BasePydanticSettings, SettingsConfigDict


class BaseSettings(BasePydanticSettings):
    BACKEND_URL: str = ""
    FRONTEND_URL: str = ""
    CHROME_EXTENSION_URL: str = ""
    DB_PORT: int = 5432
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_PASS: str = ""
    DB_USER: str = ""
    ENCRYPTION_KEY: str = ""
    SEQ_URL: str = ""
    SEQ_API_KEY: str = ""
    RABBITMQ_URL: str = ""
    REDIS_URL: str = ""
    REDIS_PORT: int = 6379
    REDIS_USER: str = ""
    REDIS_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


base_settings = BaseSettings()
