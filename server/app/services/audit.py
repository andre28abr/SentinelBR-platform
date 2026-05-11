"""Audit service: registra cada operacao relevante na tabela audit_logs.

LGPD Art. 37: o controlador deve manter registro das operacoes de tratamento.
Aqui logamos: autenticacao (sucesso/falha) e operacoes de WRITE em recursos
(hosts, alerts, actions, etc). Reads nao sao logados pra evitar ruido —
mas o tipo de info acessada eh inferivel pelo padrao de queries.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User

log = logging.getLogger(__name__)


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    # X-Forwarded-For tem prioridade pra ambientes atras de proxy/LB
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _user_agent(request: Request | None) -> str | None:
    if request is None:
        return None
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 500:
        ua = ua[:500]
    return ua


async def log_action(
    db: AsyncSession,
    *,
    action: str,
    actor: User | None = None,
    actor_email: str | None = None,
    org_id: uuid.UUID | None = None,
    target_type: str | None = None,
    target_id: str | uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
    success: bool = True,
) -> AuditLog:
    """Registra uma operacao. Commit fica a cargo do caller (mesma tx do que esta sendo logado).

    org_id default vem de actor.org_id (multi-tenancy). Pode ser sobrescrito
    explicitamente via parametro — usado em casos como login_failed onde
    nao sabemos a qual org o tentante pertence (registramos como global, NULL).
    """
    if org_id is None and actor is not None:
        org_id = actor.org_id
    entry = AuditLog(
        org_id=org_id,
        actor_user_id=actor.id if actor else None,
        actor_email=actor_email or (actor.email if actor else None),
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        details=details or {},
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
        success=success,
    )
    db.add(entry)
    log.info(
        "audit",
        extra={
            "action": action,
            "actor": str(actor.id) if actor else "anonymous",
            "target": f"{target_type}/{target_id}" if target_type else None,
            "success": success,
        },
    )
    return entry
