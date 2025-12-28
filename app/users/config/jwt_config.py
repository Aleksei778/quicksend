from pydantic_settings import BaseSettings


class PaymentSettings(BaseSettings):
    YOOKASSA_SHOP_ID: str = ""
    YOOKASSA_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

payment_settings = PaymentSettings()
