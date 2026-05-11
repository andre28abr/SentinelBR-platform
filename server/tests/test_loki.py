"""Testes integrados do cliente Loki — exigem Loki rodando.

Localmente: `make dev` sobe Loki em :3100. CI: service no workflow.
Se Loki nao responder, os testes pulam (skip) com mensagem clara.
"""

from __future__ import annotations

import datetime as dt
import uuid

import httpx
import pytest

from app.services import loki


async def _loki_alive() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as cli:
            r = await cli.get("http://localhost:3100/ready")
            return r.status_code in (200, 503)  # 503 enquanto inicializa
    except httpx.HTTPError:
        return False


@pytest.mark.asyncio
async def test_push_then_query_returns_event() -> None:
    if not await _loki_alive():
        pytest.skip("Loki nao disponivel em :3100")

    host_id = str(uuid.uuid4())
    now = dt.datetime.now(dt.UTC)
    ev = loki.IngestEvent(
        event_id=str(uuid.uuid4()),
        host_id=host_id,
        timestamp=now,
        source="sshd",
        severity="warn",
        raw="Failed password for root from 1.2.3.4 port 22 ssh2",
        fields={"user.name": "root", "source.ip": "1.2.3.4"},
    )

    await loki.push([ev])

    # Loki tem ingestion delay pequeno (geralmente <1s, ate 2s)
    import asyncio
    await asyncio.sleep(2)

    got = await loki.query_for_host(host_id, source="sshd", since=now - dt.timedelta(minutes=1))
    assert len(got) == 1, f"esperava 1 evento, veio {len(got)}: {got}"
    assert got[0].event_id == ev.event_id
    assert got[0].fields["user.name"] == "root"
    assert got[0].raw == ev.raw


@pytest.mark.asyncio
async def test_query_unknown_host_returns_empty() -> None:
    if not await _loki_alive():
        pytest.skip("Loki nao disponivel em :3100")

    got = await loki.query_for_host(str(uuid.uuid4()))
    assert got == []
