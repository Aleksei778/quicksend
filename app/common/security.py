from fastapi.security import HTTPBearer
from cryptography.fernet import Fernet

from config import ENCRYPTION_KEY


security = HTTPBearer()

key = ENCRYPTION_KEY.encode()
fernet = Fernet(key)

def encrypt(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()
