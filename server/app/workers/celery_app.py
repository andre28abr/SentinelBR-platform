"""Celery app + beat schedule.

Como rodar:
    make worker     # processa tarefas (registradas em app.workers.*)
    make beat       # scheduler que dispara periodicas (rule evaluation)

Em prod ambos rodam como container/service separado. Broker = Redis (ADR-006).
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import schedule

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sentinelbr",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.detect",
        "app.workers.retention",
        "app.workers.vuln",
        "app.workers.yara_schedule",
        "app.workers.tools_schedule",
    ],
)


def _maybe_schedule(name: str, task: str, interval: int) -> dict | None:
    """Retorna entry pro beat_schedule se interval > 0, senao None (desativa)."""
    if interval <= 0:
        return None
    return {"task": task, "schedule": schedule(run_every=float(interval))}

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    beat_schedule={
        k: v
        for k, v in {
            "detect-every-30s": {
                "task": "app.workers.detect.run_cycle",
                "schedule": schedule(run_every=30.0),
            },
            # Retencao roda 1x por dia (LGPD Art. 16). Em prod ajustar pra hora especifica.
            "retention-daily": {
                "task": "app.workers.retention.cleanup_audit_logs",
                "schedule": schedule(run_every=86400.0),
            },
            # YARA scheduled scan: 1x por dia em todos hosts ativos (paths via env).
            "yara-scheduled-scan": {
                "task": "app.workers.yara_schedule.schedule_yara_scans",
                "schedule": schedule(run_every=float(settings.yara_scheduled_interval_seconds)),
            },
            # Fase H8 — audits Tier 1+2 periodicos (intervalos via env, 0=off).
            "rkhunter-scheduled": _maybe_schedule(
                "rkhunter", "app.workers.tools_schedule.schedule_rkhunter",
                settings.rkhunter_scheduled_interval_seconds,
            ),
            "chkrootkit-scheduled": _maybe_schedule(
                "chkrootkit", "app.workers.tools_schedule.schedule_chkrootkit",
                settings.chkrootkit_scheduled_interval_seconds,
            ),
            "aide-scheduled": _maybe_schedule(
                "aide", "app.workers.tools_schedule.schedule_aide",
                settings.aide_scheduled_interval_seconds,
            ),
            "lynis-scheduled": _maybe_schedule(
                "lynis", "app.workers.tools_schedule.schedule_lynis",
                settings.lynis_scheduled_interval_seconds,
            ),
        }.items()
        if v is not None
    },
)
