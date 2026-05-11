"""Geracao e validacao de enrollment tokens.

Fluxo:
    1. Admin no web -> POST /hosts/{id}/enrollment-token -> server gera token random,
       guarda hash em hosts.enrollment_token, expiracao em hosts.enrollment_token_expires_at.
    2. Agent CLI -> POST /agents/enroll com {token, hostname} -> server valida token (timing-safe),
       gera client cert via PKI, retorna {host_id, ca_cert, client_cert, client_key, grpc_endpoint}.
       Marca enrolled_at, zera enrollment_token (one-shot).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Host

TOKEN_BYTES = 32  # 256 bits
TOKEN_TTL_MINUTES = 60


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def mint_token(db: AsyncSession, host: Host) -> tuple[str, dt.datetime]:
    """Gera token e armazena hash. Retorna (token_plain, expires_at)."""
    token = secrets.token_urlsafe(TOKEN_BYTES)
    expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(minutes=TOKEN_TTL_MINUTES)

    host.enrollment_token = _hash_token(token)
    host.enrollment_token_expires_at = expires_at
    await db.commit()
    return token, expires_at


async def validate_and_consume(db: AsyncSession, token: str) -> Host | None:
    """Valida token (timing-safe) e marca como consumido. Retorna Host ou None se invalido/expirado.

    Marca enrolled_at, zera enrollment_token (one-shot — segundo uso falha).
    """
    token_hash = _hash_token(token)
    now = dt.datetime.now(dt.UTC)

    result = await db.execute(
        select(Host).where(
            Host.enrollment_token.is_not(None),
            Host.enrollment_token_expires_at > now,
        )
    )
    candidates = list(result.scalars().all())

    matched: Host | None = None
    for h in candidates:
        if h.enrollment_token and hmac.compare_digest(h.enrollment_token, token_hash):
            matched = h
            break

    if matched is None:
        return None

    matched.enrollment_token = None
    matched.enrollment_token_expires_at = None
    matched.enrolled_at = now
    matched.status = "active"
    await db.commit()
    await db.refresh(matched)
    return matched


def install_command(
    host_id: uuid.UUID, token: str, server_endpoint: str, grpc_endpoint: str
) -> str:
    """Comando que o usuario cola no host pra enrollar. Mostra em /hosts/:id."""
    return (
        f"sudo sentinel-agent enroll \\\n"
        f"  --server={server_endpoint} \\\n"
        f"  --grpc={grpc_endpoint} \\\n"
        f"  --token={token}"
    )
