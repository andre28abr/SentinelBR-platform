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
    include=["app.workers.detect"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_send_task_events=True,
    task_send_sent_event=True,
    beat_schedule={
        "detect-every-30s": {
            "task": "app.workers.detect.run_cycle",
            "schedule": schedule(run_every=30.0),
        },
    },
)
