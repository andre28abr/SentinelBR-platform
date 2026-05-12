"""Orquestra a avaliacao das regras contra todos os hosts ativos.

Fluxo:
    1. Para cada regra carregada, para cada host ativo:
        a. Query eventos no Loki dentro da janela da regra
        b. Avalia regra (filter + aggregate)
        c. Para cada AlertCandidate:
            - Se ja existe um alert OPEN com mesma (host, rule, dedup_key)
              -> update count/last_event_at
            - Senao -> insert novo alerta

Eh chamado pela tarefa Celery 'detect.run_cycle' a cada N segundos.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import Alert, Host
from app.services import loki, policy
from app.services.rules.evaluator import AlertCandidate, evaluate
from app.services.rules.loader import Rule, load_default_rules

log = logging.getLogger(__name__)


async def _upsert_alert(db: AsyncSession, host_id: str, candidate: AlertCandidate) -> Alert:
    """Cria ou atualiza alert. Atualiza se ja existe um OPEN com mesma dedup_key."""
    dedup = candidate.dedup_key()
    existing = (
        await db.execute(
            select(Alert).where(
                Alert.host_id == host_id,
                Alert.rule_id == candidate.rule.id,
                Alert.dedup_key == dedup,
                Alert.status == "open",
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.count = candidate.count
        existing.last_event_at = candidate.last_event_at
        existing.description = candidate.description()
        existing.context = candidate.group_key
        return existing

    alert = Alert(
        host_id=host_id,
        rule_id=candidate.rule.id,
        rule_name=candidate.rule.name,
        severity=candidate.rule.severity,
        description=candidate.description(),
        count=candidate.count,
        first_event_at=candidate.first_event_at,
        last_event_at=candidate.last_event_at,
        status="open",
        context=candidate.group_key,
        dedup_key=dedup,
    )
    db.add(alert)
    return alert


async def evaluate_for_host(db: AsyncSession, host: Host, rules: list[Rule]) -> list[Alert]:
    alerts_changed: list[Alert] = []
    for rule in rules:
        since = dt.datetime.now(dt.UTC) - dt.timedelta(seconds=rule.window_seconds)
        try:
            events = await loki.query_for_host(
                host_id=str(host.id),
                source=rule.source,
                since=since,
                limit=1000,
            )
        except httpx.HTTPError as e:
            log.warning("Loki query falhou para host=%s rule=%s: %s", host.id, rule.id, e)
            continue

        for candidate in evaluate(rule, events):
            alert = await _upsert_alert(db, str(host.id), candidate)
            await db.flush()  # garante alert.id pra usar como FK na Action
            await policy.maybe_create_action(db, alert)
            alerts_changed.append(alert)

    return alerts_changed


_MAX_PARALLEL_HOSTS = 8  # limita conexoes DB simultaneas no pool


async def _evaluate_host_isolated(host: Host, rules: list[Rule]) -> int:
    """Roda evaluate_for_host pra 1 host com session isolada.

    Cada host usa sua propria session — async sessions do SQLAlchemy nao
    sao safe entre tasks. Isolar permite asyncio.gather sem corrupcao.
    """
    async with SessionLocal() as db:
        try:
            changed = await evaluate_for_host(db, host, rules)
            await db.commit()
            return len(changed)
        except Exception:
            await db.rollback()
            log.exception("falha avaliando host %s", host.id)
            return 0


async def run_cycle() -> int:
    """Roda um ciclo completo de deteccao em todos hosts ativos.

    Hosts sao avaliados em paralelo (limitado a _MAX_PARALLEL_HOSTS pra nao
    exaurir o pool DB). Retorna numero de alerts criados/atualizados.
    """
    rules = load_default_rules()
    if not rules:
        log.warning("nenhuma regra carregada — pulando ciclo")
        return 0

    async with SessionLocal() as db:
        hosts = (
            await db.execute(select(Host).where(Host.status == "active"))
        ).scalars().all()

    if not hosts:
        return 0

    sem = asyncio.Semaphore(_MAX_PARALLEL_HOSTS)

    async def _bounded(host: Host) -> int:
        async with sem:
            return await _evaluate_host_isolated(host, rules)

    counts = await asyncio.gather(*(_bounded(h) for h in hosts))
    total = sum(counts)

    log.info(
        "detection cycle: %d alerts em %d hosts (paralelo %d) e %d regras",
        total, len(hosts), _MAX_PARALLEL_HOSTS, len(rules),
    )
    return total
