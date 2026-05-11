"""Celery task pra rodar scan de vulnerabilidades de forma assincrona.

Disparado quando o agente envia inventory (em vez de bloquear o RPC). Pode tambem
ser agendado via beat (1x dia) pra re-scan quando OSV ganha novos CVEs.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.services import vuln_scan
from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name="app.workers.vuln.scan_host")
def scan_host(host_id: str) -> dict:
    try:
        return asyncio.run(vuln_scan.scan_host(uuid.UUID(host_id)))
    except Exception as e:  # noqa: BLE001
        log.exception("scan_host falhou: %s", e)
        return {"error": str(e)}
