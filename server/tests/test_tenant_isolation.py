"""Tenant isolation: usuario da Org A nao consegue ver/modificar recursos da Org B.

Garante que multi-tenancy esta enforcement-correta nos endpoints REST.
"""

from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Action, Alert, Host, Organization, User
from app.services.auth import hash_password


async def _login(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return r.json()["access_token"]


async def _setup_two_orgs(db: AsyncSession) -> tuple[Organization, User, Organization, User]:
    """Cria 2 orgs com 1 user admin cada."""
    org_a = Organization(name="Org A", slug="org-a")
    org_b = Organization(name="Org B", slug="org-b")
    db.add_all([org_a, org_b])
    await db.flush()

    user_a = User(
        org_id=org_a.id, email="a@test.io", password_hash=hash_password("teste1234"),
        name="User A", role="admin",
    )
    user_b = User(
        org_id=org_b.id, email="b@test.io", password_hash=hash_password("teste1234"),
        name="User B", role="admin",
    )
    db.add_all([user_a, user_b])
    await db.commit()
    await db.refresh(user_a)
    await db.refresh(user_b)
    return org_a, user_a, org_b, user_b


@pytest.mark.asyncio
async def test_list_hosts_isolated_per_org(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, org_b, user_b = await _setup_two_orgs(db_session)
    db_session.add(Host(org_id=org_a.id, name="ha", hostname="ha.local", status="active"))
    db_session.add(Host(org_id=org_b.id, name="hb", hostname="hb.local", status="active"))
    await db_session.commit()

    token_a = await _login(client, user_a.email, "teste1234")
    r_a = await client.get(
        "/api/v1/hosts", headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r_a.status_code == 200
    body_a = r_a.json()
    assert len(body_a) == 1
    assert body_a[0]["name"] == "ha"

    token_b = await _login(client, user_b.email, "teste1234")
    r_b = await client.get(
        "/api/v1/hosts", headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r_b.status_code == 200
    body_b = r_b.json()
    assert len(body_b) == 1
    assert body_b[0]["name"] == "hb"


@pytest.mark.asyncio
async def test_get_host_cross_org_returns_404(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, org_b, _ = await _setup_two_orgs(db_session)
    host_b = Host(org_id=org_b.id, name="hb", hostname="hb.local", status="active")
    db_session.add(host_b)
    await db_session.commit()
    await db_session.refresh(host_b)

    token_a = await _login(client, user_a.email, "teste1234")
    # User A tenta acessar host de Org B — deve dar 404 (nao 403, pra nao vazar existencia)
    r = await client.get(
        f"/api/v1/hosts/{host_b.id}", headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_alerts_count_isolated(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, org_b, user_b = await _setup_two_orgs(db_session)
    host_a = Host(org_id=org_a.id, name="ha", hostname="ha.local", status="active")
    host_b = Host(org_id=org_b.id, name="hb", hostname="hb.local", status="active")
    db_session.add_all([host_a, host_b])
    await db_session.commit()
    await db_session.refresh(host_a)
    await db_session.refresh(host_b)

    now = dt.datetime.now(dt.UTC)
    # 2 alerts pra org A, 1 pra org B
    db_session.add(Alert(
        host_id=host_a.id, rule_id="r1", rule_name="r1", severity="high",
        description="x", count=1, first_event_at=now, last_event_at=now,
        status="open", context={}, dedup_key="a1",
    ))
    db_session.add(Alert(
        host_id=host_a.id, rule_id="r2", rule_name="r2", severity="high",
        description="x", count=1, first_event_at=now, last_event_at=now,
        status="open", context={}, dedup_key="a2",
    ))
    db_session.add(Alert(
        host_id=host_b.id, rule_id="r1", rule_name="r1", severity="high",
        description="x", count=1, first_event_at=now, last_event_at=now,
        status="open", context={}, dedup_key="b1",
    ))
    await db_session.commit()

    token_a = await _login(client, user_a.email, "teste1234")
    r = await client.get(
        "/api/v1/alerts/count", headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.json() == {"open": 2, "total": 2}

    token_b = await _login(client, user_b.email, "teste1234")
    r = await client.get(
        "/api/v1/alerts/count", headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.json() == {"open": 1, "total": 1}


@pytest.mark.asyncio
async def test_actions_for_other_org_host_returns_404(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, org_b, _ = await _setup_two_orgs(db_session)
    host_b = Host(org_id=org_b.id, name="hb", hostname="hb.local", status="active")
    db_session.add(host_b)
    await db_session.commit()
    await db_session.refresh(host_b)

    db_session.add(Action(
        host_id=host_b.id, action_type="block_ip", target="1.2.3.4",
        reason="x", status="pending",
    ))
    await db_session.commit()

    token_a = await _login(client, user_a.email, "teste1234")
    r = await client.get(
        f"/api/v1/hosts/{host_b.id}/actions",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_yara_scan_other_org_host_returns_404(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, org_b, _ = await _setup_two_orgs(db_session)
    host_b = Host(org_id=org_b.id, name="hb", hostname="hb.local", status="active")
    db_session.add(host_b)
    await db_session.commit()
    await db_session.refresh(host_b)

    token_a = await _login(client, user_a.email, "teste1234")
    r = await client.post(
        f"/api/v1/hosts/{host_b.id}/yara-scan",
        json={"path": "/var/www"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_host_assigns_creators_org(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    _, user_a, _, _ = await _setup_two_orgs(db_session)
    token_a = await _login(client, user_a.email, "teste1234")

    r = await client.post(
        "/api/v1/hosts",
        json={"name": "nova", "hostname": "nova.local"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "nova"

    # Verifica direto no DB que ficou na org do criador
    new_host = await db_session.get(Host, body["id"])
    assert new_host is not None
    assert new_host.org_id == user_a.org_id


@pytest.mark.asyncio
async def test_me_endpoint_returns_org_info(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, _, _ = await _setup_two_orgs(db_session)
    token = await _login(client, user_a.email, "teste1234")
    r = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["org_id"] == str(org_a.id)
    assert body["org"]["name"] == "Org A"
    assert body["org"]["slug"] == "org-a"


@pytest.mark.asyncio
async def test_organizations_list_returns_only_own(
    client: AsyncClient, db_session: AsyncSession,
) -> None:
    org_a, user_a, _, _ = await _setup_two_orgs(db_session)
    token = await _login(client, user_a.email, "teste1234")
    r = await client.get(
        "/api/v1/organizations", headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["slug"] == "org-a"
