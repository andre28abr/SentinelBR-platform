"""Celery task: agenda scans YARA periodicos pra todos os hosts ativos.

Cria 1 Action(action_type='run_yara_scan') por host x path configurado.
Idempotente — se ja existe scan 'pending' do mesmo path naquele host, pula.

Disparado pelo beat (ver beat_schedule em celery_app.py).
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Action, Host
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


def _parse_paths(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


async def _schedule_async() -> dict:
    settings = get_settings()
    paths = _parse_paths(settings.yara_scheduled_paths)
    if not paths:
        return {"hosts": 0, "actions_created": 0, "skipped": 0}

    created = 0
    skipped = 0
    async with SessionLocal() as db:
        hosts = (
            await db.execute(select(Host).where(Host.status == "active"))
        ).scalars().all()
        if not hosts:
            return {"hosts": 0, "actions_created": 0, "skipped": 0}

        host_ids = [h.id for h in hosts]
        # Antes: 1 SELECT por host x path (N x M queries). Agora: 1 SELECT batch
        # que pega todas as actions pending/sent yara desses hosts pra esses paths.
        existing_rows = (
            await db.execute(
                select(Action.host_id, Action.target).where(
                    Action.host_id.in_(host_ids),
                    Action.action_type == "run_yara_scan",
                    Action.target.in_(paths),
                    Action.status.in_(("pending", "sent")),
                )
            )
        ).all()
        existing_keys = {(r.host_id, r.target) for r in existing_rows}

        for host in hosts:
            for path in paths:
                if (host.id, path) in existing_keys:
                    skipped += 1
                    continue
                db.add(Action(
                    host_id=host.id,
                    action_type="run_yara_scan",
                    target=path,
                    reason="scheduled",
                    status="pending",
                ))
                created += 1
        await db.commit()

    log.info("yara_schedule: hosts=%d actions=%d skipped=%d", len(hosts), created, skipped)
    return {"hosts": len(hosts), "actions_created": created, "skipped": skipped}


@celery_app.task(name="app.workers.yara_schedule.schedule_yara_scans")
def schedule_yara_scans() -> dict:
    try:
        return asyncio.run(_schedule_async())
    except Exception as e:  # noqa: BLE001
        log.exception("schedule_yara_scans falhou: %s", e)
        return {"error": str(e)}
