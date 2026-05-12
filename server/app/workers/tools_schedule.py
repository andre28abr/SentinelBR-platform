"""Celery tasks: agenda audits periodicos das ferramentas Tier 1+2 (Fase H8).

Cria 1 Action por host instalado, idempotente. Disparados pelo beat com
intervalos diferentes — rkhunter diario, lynis semanal, aide diario,
chkrootkit diario.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db import SessionLocal
from app.models import Action, Host
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


async def _schedule_tool_async(action_type: str, require_field: str) -> dict:
    """Cria 1 Action(action_type) por host ATIVO que tenha require_field=True.

    Idempotente: pula se ja existe Action do mesmo type pending/sent pro host.
    Usa 1 SELECT batch (em vez de N+1) pra checar duplicatas em massa.
    """
    created = 0
    skipped = 0
    async with SessionLocal() as db:
        hosts = (
            await db.execute(
                select(Host).where(Host.status == "active")
            )
        ).scalars().all()
        eligible = [h for h in hosts if getattr(h, require_field, None)]
        if not eligible:
            return {"eligible": 0, "actions_created": 0, "skipped": 0}

        eligible_ids = [h.id for h in eligible]
        # Batch: pega host_ids que JA tem action pending/sent desse tipo.
        existing_host_ids = set(
            (
                await db.execute(
                    select(Action.host_id).where(
                        Action.host_id.in_(eligible_ids),
                        Action.action_type == action_type,
                        Action.status.in_(("pending", "sent")),
                    )
                )
            ).scalars().all()
        )

        for host in eligible:
            if host.id in existing_host_ids:
                skipped += 1
                continue
            db.add(Action(
                host_id=host.id,
                action_type=action_type,
                target=action_type,
                reason="scheduled",
                status="pending",
            ))
            created += 1
        await db.commit()

    log.info(
        "%s schedule: eligible=%d actions=%d skipped=%d",
        action_type, len(eligible), created, skipped,
    )
    return {"eligible": len(eligible), "actions_created": created, "skipped": skipped}


@celery_app.task(name="app.workers.tools_schedule.schedule_rkhunter")
def schedule_rkhunter() -> dict:
    try:
        return asyncio.run(_schedule_tool_async("run_rkhunter_scan", "rkhunter_installed"))
    except Exception as e:  # noqa: BLE001
        log.exception("schedule_rkhunter falhou: %s", e)
        return {"error": str(e)}


@celery_app.task(name="app.workers.tools_schedule.schedule_lynis")
def schedule_lynis() -> dict:
    try:
        return asyncio.run(_schedule_tool_async("run_lynis_audit", "lynis_installed"))
    except Exception as e:  # noqa: BLE001
        log.exception("schedule_lynis falhou: %s", e)
        return {"error": str(e)}


@celery_app.task(name="app.workers.tools_schedule.schedule_chkrootkit")
def schedule_chkrootkit() -> dict:
    try:
        return asyncio.run(_schedule_tool_async("run_chkrootkit_scan", "chkrootkit_installed"))
    except Exception as e:  # noqa: BLE001
        log.exception("schedule_chkrootkit falhou: %s", e)
        return {"error": str(e)}


@celery_app.task(name="app.workers.tools_schedule.schedule_aide")
def schedule_aide() -> dict:
    try:
        return asyncio.run(_schedule_tool_async("run_aide_check", "aide_installed"))
    except Exception as e:  # noqa: BLE001
        log.exception("schedule_aide falhou: %s", e)
        return {"error": str(e)}
