"""Helpers compartilhados pra criar Actions com idempotencia + audit.

Antes: 6 routers (clamav, yara, fail2ban, firewall, tools, vulnerabilities)
duplicavam o pattern get-host-or-404 + check pending + create Action +
audit + commit. ~250 LoC repetidas.

Agora: pending_action_exists() + create_pending_action() centralizam tudo.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Action, Host, User
from app.services import audit


async def pending_action_exists(
    db: AsyncSession,
    *,
    host_id: uuid.UUID,
    action_type: str,
    target: str | None = None,
    statuses: tuple[str, ...] = ("pending", "sent"),
) -> bool:
    """True se ja existe action do mesmo tipo (e target opcional) em status."""
    stmt = select(Action.id).where(
        Action.host_id == host_id,
        Action.action_type == action_type,
        Action.status.in_(statuses),
    )
    if target is not None:
        stmt = stmt.where(Action.target == target)
    result = await db.execute(stmt)
    return result.first() is not None


async def create_pending_action(
    db: AsyncSession,
    *,
    host: Host,
    actor: User,
    request: Request,
    action_type: str,
    target: str,
    reason: str = "manual_ui",
    audit_action: str | None = None,
    audit_details: dict[str, Any] | None = None,
    idempotency_check_target: bool = True,
    conflict_detail: str = "ja existe action pendente do mesmo tipo nesse host",
) -> Action:
    """Cria Action(pending) com idempotency check + audit log.

    Args:
        host: host alvo (assume-se que ja foi validado cross-org pelo router).
        actor: user logado (current).
        request: HTTP request (pra capturar IP/UA no audit).
        action_type: ex 'run_clamav_scan', 'fail2ban_unban'.
        target: identificador do alvo (path do scan, "jail:ip", etc).
        reason: motivo (default 'manual_ui').
        audit_action: nome da entry no audit_log (default = f'{action_type}_triggered').
        audit_details: dict extra pra audit (action_id eh adicionado automaticamente).
        idempotency_check_target: se False, idempotency considera so action_type
            (sem target) — usado pra rkhunter/lynis/aide/chkrootkit que tem
            target=action_type (so 1 por host por vez).
        conflict_detail: mensagem 409 customizada.

    Raises:
        HTTPException(409) se ja existe action pending/sent.
    """
    check_target = target if idempotency_check_target else None
    if await pending_action_exists(
        db, host_id=host.id, action_type=action_type, target=check_target,
    ):
        raise HTTPException(status_code=409, detail=conflict_detail)

    action = Action(
        host_id=host.id,
        action_type=action_type,
        target=target,
        reason=reason,
        status="pending",
    )
    db.add(action)
    await db.flush()

    full_details = {**(audit_details or {}), "action_id": str(action.id)}
    await audit.log_action(
        db,
        action=audit_action or f"{action_type}_triggered",
        actor=actor,
        request=request,
        target_type="host",
        target_id=host.id,
        details=full_details,
    )
    await db.commit()
    await db.refresh(action)
    return action


async def get_host_in_org_or_404(
    db: AsyncSession, host_id: uuid.UUID, org_id: uuid.UUID,
) -> Host:
    """Helper compartilhado — substitui _host_in_org_or_404 espalhado em
    actions/alerts/events/clamav/yara/firewall/fail2ban/tools/vulnerabilities."""
    host = await db.get(Host, host_id)
    if host is None or host.org_id != org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    return host
