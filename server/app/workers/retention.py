"""Tarefa Celery de retencao: apaga audit_logs antigos (LGPD Art. 16 — descarte
apos finalidade cumprida).

Schedule default: diario as 03:00 UTC. Retencao default: 180 dias (configuravel
via env SENTINELBR_AUDIT_RETENTION_DAYS).
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging

from sqlalchemy import delete

from app.config import get_settings
from app.db import SessionLocal
from app.models import AuditLog
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


async def _cleanup() -> int:
    settings = get_settings()
    days = settings.audit_retention_days
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)

    async with SessionLocal() as db:
        result = await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
        deleted = result.rowcount or 0
        await db.commit()

    log.info("retention: %d audit_logs apagados (>%dd)", deleted, days)
    return deleted


@celery_app.task(name="app.workers.retention.cleanup_audit_logs")
def cleanup_audit_logs() -> int:
    try:
        return asyncio.run(_cleanup())
    except Exception as e:  # noqa: BLE001
        log.exception("retention falhou: %s", e)
        return 0
