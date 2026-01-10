import base64
import hashlib
from fastapi.security import HTTPBearer
from cryptography.fernet import Fernet

from common.utils.config import base_config

security = HTTPBearer(auto_error=False)

raw_key = base_config.ENCRYPTION_KEY.encode()
key = base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())
fernet = Fernet(key)


def encrypt(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()
