"""Testes da policy de auto-block + endpoints REST de actions."""

from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Action, Alert, Host, User
from app.services import policy


async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


async def _seed_host(db: AsyncSession) -> Host:
    h = Host(name="h1", hostname="h1.example.com", status="active")
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


async def _seed_alert(
    db: AsyncSession, host: Host, *, rule_id: str, ip: str | None = "1.2.3.4"
) -> Alert:
    now = dt.datetime.now(dt.UTC)
    ctx = {"source.ip": ip} if ip else {}
    a = Alert(
        host_id=host.id,
        rule_id=rule_id,
        rule_name=rule_id,
        severity="high",
        description="x",
        count=5,
        first_event_at=now,
        last_event_at=now,
        status="open",
        context=ctx,
        dedup_key=f"source.ip={ip}",
    )
    db.add(a)
    await db.commit()
    await db.refresh(a)
    return a


@pytest.mark.asyncio
async def test_policy_creates_block_for_brute_force_ip(
    db_session: AsyncSession,
) -> None:
    host = await _seed_host(db_session)
    alert = await _seed_alert(db_session, host, rule_id="ssh_brute_force_ip", ip="1.2.3.4")

    action = await policy.maybe_create_action(db_session, alert)
    await db_session.commit()

    assert action is not None
    assert action.action_type == "block_ip"
    assert action.target == "1.2.3.4"
    assert action.status == "pending"


@pytest.mark.asyncio
async def test_policy_idempotent_no_duplicate_block(db_session: AsyncSession) -> None:
    host = await _seed_host(db_session)
    alert = await _seed_alert(db_session, host, rule_id="ssh_brute_force_ip", ip="1.2.3.4")

    a1 = await policy.maybe_create_action(db_session, alert)
    await db_session.commit()
    a2 = await policy.maybe_create_action(db_session, alert)
    await db_session.commit()

    assert a1 is not None
    assert a2 is None  # ja existe pending pro mesmo IP


@pytest.mark.asyncio
async def test_policy_skips_non_matching_rules(db_session: AsyncSession) -> None:
    host = await _seed_host(db_session)
    alert = await _seed_alert(
        db_session, host, rule_id="ssh_brute_force_user", ip="1.2.3.4"
    )

    # ssh_brute_force_user nao esta no _BLOCK_IP_RULE_IDS
    action = await policy.maybe_create_action(db_session, alert)
    assert action is None


@pytest.mark.asyncio
async def test_policy_skips_alert_without_source_ip(db_session: AsyncSession) -> None:
    host = await _seed_host(db_session)
    alert = await _seed_alert(db_session, host, rule_id="ssh_brute_force_ip", ip=None)
    action = await policy.maybe_create_action(db_session, alert)
    assert action is None


@pytest.mark.asyncio
async def test_list_actions_for_host(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    db_session.add(Action(
        host_id=host.id, action_type="block_ip", target="1.2.3.4",
        reason="test", status="pending",
    ))
    db_session.add(Action(
        host_id=host.id, action_type="block_ip", target="5.6.7.8",
        reason="test", status="executed",
    ))
    await db_session.commit()

    token = await _login(client, admin_user)
    r = await client.get(
        f"/api/v1/hosts/{host.id}/actions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2


@pytest.mark.asyncio
async def test_policy_creates_quarantine_for_yara_critical(
    db_session: AsyncSession,
) -> None:
    host = await _seed_host(db_session)
    now = dt.datetime.now(dt.UTC)
    a = Alert(
        host_id=host.id,
        rule_id="yara_critical_match",
        rule_name="YARA critical",
        severity="critical",
        description="webshell detectada",
        count=1,
        first_event_at=now,
        last_event_at=now,
        status="open",
        context={"yara.rule_name": "WebshellPHP", "file.path": "/var/www/x.php"},
        dedup_key="WebshellPHP|/var/www/x.php",
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    action = await policy.maybe_create_action(db_session, a)
    await db_session.commit()

    assert action is not None
    assert action.action_type == "quarantine_file"
    assert action.target == "/var/www/x.php"
    assert "WebshellPHP" in action.reason


@pytest.mark.asyncio
async def test_policy_quarantine_idempotent(db_session: AsyncSession) -> None:
    host = await _seed_host(db_session)
    now = dt.datetime.now(dt.UTC)
    a = Alert(
        host_id=host.id,
        rule_id="yara_critical_match",
        rule_name="YARA critical",
        severity="critical",
        description="x",
        count=1,
        first_event_at=now,
        last_event_at=now,
        status="open",
        context={"yara.rule_name": "Miner", "file.path": "/var/tmp/xmrig"},  # noqa: S108
        dedup_key="Miner|/var/tmp/xmrig",
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    a1 = await policy.maybe_create_action(db_session, a)
    await db_session.commit()
    a2 = await policy.maybe_create_action(db_session, a)
    await db_session.commit()

    assert a1 is not None
    assert a2 is None  # ja tem pending


@pytest.mark.asyncio
async def test_yara_scan_endpoint_creates_action(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    token = await _login(client, admin_user)

    r = await client.post(
        f"/api/v1/hosts/{host.id}/yara-scan",
        json={"path": "/var/www", "reason": "manual_ui"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["action_type"] == "run_yara_scan"
    assert body["target"] == "/var/www"
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_yara_scan_endpoint_idempotent(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    token = await _login(client, admin_user)

    r1 = await client.post(
        f"/api/v1/hosts/{host.id}/yara-scan",
        json={"path": "/var/www"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 202

    r2 = await client.post(
        f"/api/v1/hosts/{host.id}/yara-scan",
        json={"path": "/var/www"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_yara_scan_endpoint_404_unknown_host(
    client: AsyncClient, admin_user: User
) -> None:
    token = await _login(client, admin_user)
    r = await client.post(
        "/api/v1/hosts/00000000-0000-0000-0000-000000000000/yara-scan",
        json={"path": "/var/www"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_revert_executed_creates_unblock(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = await _seed_host(db_session)
    a = Action(
        host_id=host.id, action_type="block_ip", target="9.9.9.9",
        reason="test", status="executed",
    )
    db_session.add(a)
    await db_session.commit()
    await db_session.refresh(a)

    token = await _login(client, admin_user)
    r = await client.patch(
        f"/api/v1/actions/{a.id}",
        json={"status": "reverted"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text

    unblocks = (
        await db_session.execute(
            select(Action).where(Action.action_type == "unblock_ip")
        )
    ).scalars().all()
    assert len(unblocks) == 1
    assert unblocks[0].target == "9.9.9.9"
    assert unblocks[0].status == "pending"
