"""Testes do REST /api/v1/alerts (CRUD + filters + count)."""

from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Host, User


async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


async def _seed_host(db: AsyncSession, name: str = "host1") -> Host:
    h = Host(name=name, hostname=f"{name}.example.com", status="active")
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


_alert_counter = 0


async def _seed_alert(
    db: AsyncSession, host: Host, *, severity: str = "high", st: str = "open"
) -> Alert:
    global _alert_counter
    _alert_counter += 1
    now = dt.datetime.now(dt.UTC)
    a = Alert(
        host_id=host.id,
        rule_id="ssh_brute_force_ip",
        rule_name="SSH brute-force",
        severity=severity,
        description="5 falhas do mesmo IP",
        count=5,
        first_event_at=now,
        last_event_at=now,
        status=st,
        context={"source.ip": f"203.0.113.{_alert_counter}"},
        dedup_key=f"source.ip=203.0.113.{_alert_counter}",
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


@pytest.mark.asyncio
async def test_list_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/alerts")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_returns_recent_first(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    await _seed_alert(db_session, host, severity="high")
    await _seed_alert(db_session, host, severity="medium", st="resolved")

    token = await _login(client, admin_user)
    r = await client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2


@pytest.mark.asyncio
async def test_list_filters_by_status(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    await _seed_alert(db_session, host, st="open")
    await _seed_alert(db_session, host, st="resolved")

    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/alerts?status=open",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = r.json()
    assert len(body) == 1
    assert body[0]["status"] == "open"


@pytest.mark.asyncio
async def test_count_returns_open_and_total(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    await _seed_alert(db_session, host, st="open")
    await _seed_alert(db_session, host, st="open")
    await _seed_alert(db_session, host, st="resolved")

    token = await _login(client, admin_user)
    r = await client.get("/api/v1/alerts/count", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == {"open": 2, "total": 3}


@pytest.mark.asyncio
async def test_patch_updates_status(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    alert = await _seed_alert(db_session, host)

    token = await _login(client, admin_user)
    r = await client.patch(
        f"/api/v1/alerts/{alert.id}",
        json={"status": "acknowledged"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "acknowledged"


@pytest.mark.asyncio
async def test_get_404_for_unknown(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/alerts/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
