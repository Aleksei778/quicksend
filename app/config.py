from celery.bin.base import CeleryOption
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../.env")

DB_PORT = os.getenv("DB_PORT")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

JWT_ACCESS_SECRET_FOR_AUTH = os.getenv("JWT_ACCESS_SECRET_FOR_AUTH")
JWT_REFRESH_SECRET_FOR_AUTH = os.getenv("JWT_REFRESH_SECRET_FOR_AUTH")
ACCESS_TOKEN_EXPIRES_MINUTES = 30
REFRESH_TOKEN_EXPIRES_DAYS = 7
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

SECRET_FOR_MANAGER = os.getenv("SECRET_FOR_MANAGER")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL")

TINKOFF_TERMINAL_KEY = os.getenv("TINKOFF_TERMINAL_KEY")
TINKOFF_SECRET_KEY = os.getenv("TINKOFF_SECRET_KEY")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID")

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

RABBITMQ

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]

CORS_ORIGINS = [
    "http://127.0.0.1:8000",
    "chrome-extension://fekaiggohacnhgaleajohgpipbmbiaca",
    "https://f069-78-30-229-174.ngrok-free.app",
    "https://mail.google.com",
]

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

CELERY_BROKER_URL = os.getenv()
