"""Policy module: dado um Alert recem-criado/atualizado, decide se cria uma Action.

MVP: politicas hard-coded:
  - SSH brute-force (com source.ip no contexto) -> block_ip
  - YARA critical match (com file.path no contexto) -> quarantine_file

Idempotente: nao cria action duplicada se ja existe uma 'pending' ou 'sent'
pro mesmo (host, action_type, target).

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

# Regras YARA que disparam quarentena automatica.
_QUARANTINE_RULE_IDS = frozenset({
    "yara_critical_match",
})


async def _has_open_action(
    db: AsyncSession, host_id: uuid.UUID, action_type: str, target: str,
) -> bool:
    result = await db.execute(
        select(Action.id).where(
            Action.host_id == host_id,
            Action.action_type == action_type,
            Action.target == target,
            Action.status.in_(("pending", "sent", "executed")),
        )
    )
    return result.first() is not None


async def maybe_create_action(db: AsyncSession, alert: Alert) -> Action | None:
    """Cria uma Action se o Alert dispara alguma policy. Idempotente."""
    if alert.rule_id in _BLOCK_IP_RULE_IDS:
        return await _create_block_ip(db, alert)
    if alert.rule_id in _QUARANTINE_RULE_IDS:
        return await _create_quarantine(db, alert)
    return None


async def _create_block_ip(db: AsyncSession, alert: Alert) -> Action | None:
    ip = alert.context.get("source.ip") if isinstance(alert.context, dict) else None
    if not ip:
        return None
    if await _has_open_action(db, alert.host_id, "block_ip", ip):
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


async def _create_quarantine(db: AsyncSession, alert: Alert) -> Action | None:
    ctx = alert.context if isinstance(alert.context, dict) else {}
    file_path = ctx.get("file.path")
    if not file_path:
        return None
    if await _has_open_action(db, alert.host_id, "quarantine_file", file_path):
        return None
    rule_name = ctx.get("yara.rule_name", "unknown")
    action = Action(
        host_id=alert.host_id,
        alert_id=alert.id,
        action_type="quarantine_file",
        target=file_path,
        reason=f"alert:{alert.rule_id}:{rule_name}",
        status="pending",
    )
    db.add(action)
    log.info(
        "policy: action quarantine_file criada host=%s file=%s rule=%s",
        alert.host_id, file_path, rule_name,
    )
    return action
