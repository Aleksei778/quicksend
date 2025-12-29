from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../../.env")

DB_PORT = os.getenv("DB_PORT")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

JWT_ACCESS_TOKEN_SECRET_FOR_AUTH = os.getenv("JWT_ACCESS_SECRET_FOR_AUTH")
JWT_REFRESH_TOKEN_SECRET_FOR_AUTH = os.getenv("JWT_REFRESH_SECRET_FOR_AUTH")
JWT_ACCESS_TOKEN_EXPIRES_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRES_DAYS = 7
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

BASE_URL = os.getenv("BASE_URL")

CORS_ORIGINS = [
    "http://127.0.0.1:8000",
    "chrome-extension://fekaiggohacnhgaleajohgpipbmbiaca",
    "https://f069-78-30-229-174.ngrok-free.app",
]

ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

GOOGLE_AUTH_SCOPES = os.getenv("GOOGLE_AUTH_SCOPES")
GOOGLE_AUTHORIZE_URL = os.getenv("GOOGLE_AUTHORIZE_URL")
GOOGLE_ACCESS_TOKEN_URL = os.getenv("GOOGLE_ACCESS_TOKEN_URL")
GOOGLE_REDIRECT_URL = os.getenv("GOOGLE_REDIRECT_URL")
GOOGLE_CONFIGURATION_URL = os.getenv("GOOGLE_CONFIGURATION_URL")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_USERINFO_URL = os.getenv("GOOGLE_USERINFO_URL")

SEQ_URL=os.getenv("SEQ_URL")
SEQ_API_KEY=os.getenv("SEQ_API_KEY")
