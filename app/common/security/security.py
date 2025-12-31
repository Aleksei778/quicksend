from fastapi.security import HTTPBearer
from cryptography.fernet import Fernet

from common.config.base_config import base_settings


security = HTTPBearer()

key = base_settings.ENCRYPTION_KEY.encode()
fernet = Fernet(key)

def encrypt(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()
