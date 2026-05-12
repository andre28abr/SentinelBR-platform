import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal, TypedDict

import bcrypt
import jwt

from app.config import get_settings

TokenType = Literal["access", "refresh"]


class JWTPayload(TypedDict, total=False):
    """Payload tipado dos JWTs emitidos pelo SentinelBR.

    `jti` so eh emitido em refresh tokens (pra suporte a rotation/revocation).
    `type` discrimina access vs refresh — checado em decode_token.
    """
    sub: str
    type: TokenType
    iat: int
    exp: int
    jti: str

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


def issue_token(subject: str, token_type: TokenType, jti: str | None = None) -> str:
    """Gera JWT assinado HS256.

    Refresh tokens DEVEM ter `jti` — usado pela tabela refresh_token_jtis pra
    revocation/rotation. Pra access tokens, `jti` eh ignorado (sem state).
    """
    settings = get_settings()
    now = datetime.now(UTC)
    if token_type == "access":  # noqa: S105 (literal de discriminator, nao senha)
        exp = now + timedelta(minutes=settings.access_token_minutes)
    else:
        exp = now + timedelta(days=settings.refresh_token_days)
    payload: dict = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    if jti is not None:
        payload["jti"] = jti
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def new_jti() -> str:
    """JTI seguro pra refresh tokens (32 hex chars = 128 bits)."""
    return secrets.token_hex(16)


def decode_token(token: str, expected_type: TokenType) -> JWTPayload:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        got = payload.get("type")
        raise jwt.InvalidTokenError(f"esperado token tipo {expected_type}, veio {got}")
    return payload  # type: ignore[return-value]
