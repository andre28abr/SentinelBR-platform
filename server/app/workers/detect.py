"""Tarefa Celery que roda o ciclo de deteccao de regras.

Disparada pelo beat a cada 30s (ver celery_app.beat_schedule).
"""

from __future__ import annotations

import asyncio
import logging

from app.services.rules import engine
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="app.workers.detect.run_cycle")
def run_cycle() -> int:
    """Wrapper sync ao redor do engine.run_cycle (que eh async)."""
    try:
        return asyncio.run(engine.run_cycle())
    except Exception as e:  # noqa: BLE001
        log.exception("ciclo de deteccao falhou: %s", e)
        return 0
