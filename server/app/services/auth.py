from datetime import UTC, datetime, timedelta
from typing import Literal

import bcrypt
import jwt

from app.config import get_settings

TokenType = Literal["access", "refresh"]

# bcrypt rejeita senhas > 72 bytes. Truncamos silenciosamente para compatibilidade
# (mesmo comportamento que passlib usa por padrão).
_MAX_BCRYPT_BYTES = 72


def _truncate(plain: str) -> bytes:
    return plain.encode("utf-8")[:_MAX_BCRYPT_BYTES]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_truncate(plain), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(plain), hashed.encode())
    except ValueError:
        return False


def issue_token(subject: str, token_type: TokenType) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    if token_type == "access":
        exp = now + timedelta(minutes=settings.access_token_minutes)
    else:
        exp = now + timedelta(days=settings.refresh_token_days)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: TokenType) -> dict:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"esperado token tipo {expected_type}, veio {payload.get('type')}")
    return payload
