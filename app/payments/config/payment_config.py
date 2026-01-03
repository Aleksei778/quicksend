from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentSettings(BaseSettings):
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_API_KEY: str = ""
    PAYMENT_RETURN_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


payment_settings = PaymentSettings()
