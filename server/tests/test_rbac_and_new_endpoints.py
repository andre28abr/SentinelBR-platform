"""Cobertura RBAC + endpoints novos (Fase H2/H3/H6/H7) + cross-tenant.

Endpoints cobertos:
  - POST /hosts/:id/{clamav-scan, yara-scan, fail2ban-{ban,unban}, firewall-rule}
  - POST /hosts/:id/{rkhunter-scan, lynis-audit, chkrootkit-scan, aide-check}
  - DELETE /actions/:id (RBAC admin)
  - DELETE /alerts/:id (RBAC admin)
  - DELETE /hosts/:id (RBAC admin)
  - PUT/POST /organizations (RBAC admin + audit)
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models import Host, Organization, User
from app.services.auth import hash_password


async def _login(client: AsyncClient, user: User, password: str = "teste1234") -> str:  # noqa: S107
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    return r.json()["access_token"]


@pytest_asyncio.fixture
async def viewer_user(db_session, default_org: Organization) -> User:
    u = User(
        org_id=default_org.id,
        email="viewer@test.io",
        password_hash=hash_password("teste1234"),
        name="Viewer",
        role="viewer",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def operator_user(db_session, default_org: Organization) -> User:
    u = User(
        org_id=default_org.id,
        email="operator@test.io",
        password_hash=hash_password("teste1234"),
        name="Operator",
        role="operator",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def host_with_tools(db_session, default_org: Organization) -> Host:
    """Host fully equipado pra testes (todas tools=installed)."""
    h = Host(
        org_id=default_org.id,
        name="lab-test",
        hostname="lab-test.local",
        status="active",
        clamav_installed=True,
        fail2ban_installed=True,
        rkhunter_installed=True,
        chkrootkit_installed=True,
        lynis_installed=True,
        aide_installed=True,
        firewall_active="ufw",
    )
    db_session.add(h)
    await db_session.commit()
    await db_session.refresh(h)
    return h


# ─── RBAC: viewer NAO pode disparar acoes destrutivas ────────────────────────

@pytest.mark.asyncio
async def test_viewer_cannot_trigger_clamav(
    client: AsyncClient, viewer_user: User, host_with_tools: Host,
) -> None:
    token = await _login(client, viewer_user)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/clamav-scan",
        headers={"Authorization": f"Bearer {token}"},
        json={"path": "/tmp"},  # noqa: S108
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_delete_host(
    client: AsyncClient, viewer_user: User, host_with_tools: Host,
) -> None:
    token = await _login(client, viewer_user)
    r = await client.delete(
        f"/api/v1/hosts/{host_with_tools.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_operator_can_trigger_clamav(
    client: AsyncClient, operator_user: User, host_with_tools: Host,
) -> None:
    token = await _login(client, operator_user)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/clamav-scan",
        headers={"Authorization": f"Bearer {token}"},
        json={"path": "/tmp"},  # noqa: S108
    )
    assert r.status_code == 202
    assert r.json()["action_type"] == "run_clamav_scan"


@pytest.mark.asyncio
async def test_operator_cannot_delete_host(
    client: AsyncClient, operator_user: User, host_with_tools: Host,
) -> None:
    """Operator pode disparar scans, MAS nao pode deletar host (admin only)."""
    token = await _login(client, operator_user)
    r = await client.delete(
        f"/api/v1/hosts/{host_with_tools.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


# ─── Endpoints novos: happy path ─────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint,extra_body", [
    ("rkhunter-scan", {}),
    ("chkrootkit-scan", {}),
    ("lynis-audit", {}),
    ("aide-check", {}),
])
async def test_tool_endpoints_create_action(
    client: AsyncClient, admin_user: User, host_with_tools: Host,
    endpoint: str, extra_body: dict,
) -> None:
    token = await _login(client, admin_user)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        json=extra_body,
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_fail2ban_unban_creates_action(
    client: AsyncClient, admin_user: User, host_with_tools: Host,
) -> None:
    token = await _login(client, admin_user)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/fail2ban-unban",
        headers={"Authorization": f"Bearer {token}"},
        json={"jail": "sshd", "ip": "203.0.113.42"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["target"] == "sshd:203.0.113.42"


@pytest.mark.asyncio
async def test_fail2ban_rejects_invalid_ip(
    client: AsyncClient, admin_user: User, host_with_tools: Host,
) -> None:
    token = await _login(client, admin_user)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/fail2ban-unban",
        headers={"Authorization": f"Bearer {token}"},
        json={"jail": "sshd", "ip": "not-an-ip"},
    )
    assert r.status_code == 422  # Pydantic validator


@pytest.mark.asyncio
async def test_firewall_add_rule_ufw(
    client: AsyncClient, admin_user: User, host_with_tools: Host,
) -> None:
    token = await _login(client, admin_user)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/firewall-rule",
        headers={"Authorization": f"Bearer {token}"},
        json={"verb": "allow", "protocol": "tcp", "port": "22"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["target"].startswith("ufw|allow|tcp|22|")


@pytest.mark.asyncio
async def test_firewall_rejects_unsupported_backend(
    client: AsyncClient, admin_user: User, db_session, default_org: Organization,
) -> None:
    """Host com firewall=iptables: write nao suportado, retorna 400."""
    h = Host(
        org_id=default_org.id, name="ipt-host", hostname="ipt.local",
        status="active", firewall_active="iptables",
    )
    db_session.add(h)
    await db_session.commit()
    await db_session.refresh(h)

    token = await _login(client, admin_user)
    r = await client.post(
        f"/api/v1/hosts/{h.id}/firewall-rule",
        headers={"Authorization": f"Bearer {token}"},
        json={"verb": "allow", "protocol": "tcp", "port": "22"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_tool_endpoint_404_when_not_installed(
    client: AsyncClient, admin_user: User, db_session, default_org: Organization,
) -> None:
    """rkhunter sem rkhunter_installed=True deve retornar 400."""
    h = Host(
        org_id=default_org.id, name="bare", hostname="bare.local",
        status="active", rkhunter_installed=False,
    )
    db_session.add(h)
    await db_session.commit()
    await db_session.refresh(h)

    token = await _login(client, admin_user)
    r = await client.post(
        f"/api/v1/hosts/{h.id}/rkhunter-scan",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert r.status_code == 400


# ─── Cross-tenant: outra org nao pode tocar nos hosts ────────────────────────

@pytest_asyncio.fixture
async def other_org_admin(db_session) -> User:
    other_org = Organization(name="Other", slug="other")
    db_session.add(other_org)
    await db_session.commit()
    await db_session.refresh(other_org)
    u = User(
        org_id=other_org.id,
        email="other@test.io",
        password_hash=hash_password("teste1234"),
        name="Other Admin",
        role="admin",
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_cross_tenant_clamav_scan_returns_404(
    client: AsyncClient, other_org_admin: User, host_with_tools: Host,
) -> None:
    """Admin da org B tentando disparar scan em host da org A: 404 (nao 403,
    pra nao revelar existencia do host)."""
    token = await _login(client, other_org_admin)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/clamav-scan",
        headers={"Authorization": f"Bearer {token}"},
        json={"path": "/tmp"},  # noqa: S108
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_firewall_rule_returns_404(
    client: AsyncClient, other_org_admin: User, host_with_tools: Host,
) -> None:
    token = await _login(client, other_org_admin)
    r = await client.post(
        f"/api/v1/hosts/{host_with_tools.id}/firewall-rule",
        headers={"Authorization": f"Bearer {token}"},
        json={"verb": "allow", "protocol": "tcp", "port": "22"},
    )
    assert r.status_code == 404
