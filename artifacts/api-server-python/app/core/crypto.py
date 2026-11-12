import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


def _fernet() -> Fernet:
    # Key derived from JWT_SECRET: rotating that secret also invalidates stored Spotify links.
    key = base64.urlsafe_b64encode(hashlib.sha256(b"edm-spotify-link:" + settings.JWT_SECRET.encode()).digest())
    return Fernet(key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str | None:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return None
