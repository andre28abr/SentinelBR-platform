"""Policy module: dado um Alert recem-criado/atualizado, decide se cria uma Action.

MVP: politica hard-coded — alertas SSH brute-force (high severity, com source.ip
no contexto) viram block_ip pra aquele IP no host afetado. Idempotente: nao
cria action duplicada se ja existe uma 'pending' ou 'sent' pro mesmo (host, target).

Em versao futura: tabela `playbooks` com matchers configuraveis.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Action, Alert

log = logging.getLogger(__name__)

# Regras que disparam block_ip por source.ip no contexto.
_BLOCK_IP_RULE_IDS = frozenset({
    "ssh_brute_force_ip",
    "ssh_root_login_failure",
    "ssh_user_enumeration",
})


async def _has_open_block(db: AsyncSession, host_id: uuid.UUID, ip: str) -> bool:
    result = await db.execute(
        select(Action.id).where(
            Action.host_id == host_id,
            Action.action_type == "block_ip",
            Action.target == ip,
            Action.status.in_(("pending", "sent", "executed")),
        )
    )
    return result.first() is not None


async def maybe_create_action(db: AsyncSession, alert: Alert) -> Action | None:
    """Cria uma Action se o Alert dispara alguma policy. Idempotente."""
    if alert.rule_id not in _BLOCK_IP_RULE_IDS:
        return None

    ip = alert.context.get("source.ip") if isinstance(alert.context, dict) else None
    if not ip:
        return None

    if await _has_open_block(db, alert.host_id, ip):
        return None

    action = Action(
        host_id=alert.host_id,
        alert_id=alert.id,
        action_type="block_ip",
        target=ip,
        reason=f"alert:{alert.rule_id}",
        status="pending",
    )
    db.add(action)
    log.info("policy: action block_ip criada host=%s target=%s", alert.host_id, ip)
    return action
