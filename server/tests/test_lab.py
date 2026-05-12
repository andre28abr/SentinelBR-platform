"""Testes do /api/v1/lab — controle de VMs OrbStack + reset demo.

Mocka `app.services.lab._run_orb` pra nao precisar do orb instalado em CI.
"""

from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Action, Alert, AuditLog, Host, User
from app.services import lab


async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


def _enable_lab_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forca settings.lab_mode=True via lru_cache override."""
    s = get_settings()
    monkeypatch.setattr(s, "lab_mode", True)


def _disable_lab_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    s = get_settings()
    monkeypatch.setattr(s, "lab_mode", False)


# /lab/status — PUBLICO (sem auth), pra LoginPage mostrar banner antes do login


@pytest.mark.asyncio
async def test_status_is_public(client: AsyncClient,
                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem token deve retornar 200 (LoginPage le antes de logar)."""
    _disable_lab_mode(monkeypatch)
    r = await client.get("/api/v1/lab/status")
    assert r.status_code == 200
    assert r.json() == {"enabled": False}


@pytest.mark.asyncio
async def test_status_returns_enabled_when_flag_on(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_lab_mode(monkeypatch)
    r = await client.get("/api/v1/lab/status")
    assert r.status_code == 200
    assert r.json() == {"enabled": True}


# /lab/vms etc 404 quando lab_mode=false (esconde a API em prod)


@pytest.mark.asyncio
async def test_vms_404_when_lab_mode_off(
    client: AsyncClient, admin_user: User, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_lab_mode(monkeypatch)
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/lab/vms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_start_404_when_lab_mode_off(
    client: AsyncClient, admin_user: User, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _disable_lab_mode(monkeypatch)
    token = await _login(client, admin_user)
    r = await client.post(
        "/api/v1/lab/vms/lab-debian-11/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


# /lab/vms — lista (orb mockado)


@pytest.mark.asyncio
async def test_list_vms_returns_only_lab_prefixed(
    client: AsyncClient, admin_user: User, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_lab_mode(monkeypatch)
    # Formato real do orbctl list --format json (image eh objeto aninhado)
    fake_json = (
        '[{"name":"lab-debian-11","state":"running",'
        '"image":{"distro":"debian","version":"bullseye","arch":"arm64"}},'
        '{"name":"my-personal","state":"stopped",'
        '"image":{"distro":"ubuntu","version":"jammy","arch":"arm64"}},'
        '{"name":"lab-fedora","state":"stopped",'
        '"image":{"distro":"fedora","version":"43","arch":"arm64"}}]'
    )

    async def fake_run_orb(*args: str, timeout: int = 30):  # noqa: ASYNC109
        return (0, fake_json, "")

    monkeypatch.setattr(lab, "_run_orb", fake_run_orb)

    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/lab/vms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    names = [v["name"] for v in body]
    assert names == ["lab-debian-11", "lab-fedora"]  # ordenado, sem my-personal


@pytest.mark.asyncio
async def test_list_vms_502_when_orb_fails(
    client: AsyncClient, admin_user: User, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_lab_mode(monkeypatch)

    async def fake_run_orb(*args: str, timeout: int = 30):  # noqa: ASYNC109
        return (1, "", "orb: command not found")

    monkeypatch.setattr(lab, "_run_orb", fake_run_orb)

    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/lab/vms",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 502


# Validacao de VM name — bloqueia injection mesmo com argv


@pytest.mark.asyncio
async def test_start_rejects_invalid_vm_name(
    client: AsyncClient, admin_user: User, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_lab_mode(monkeypatch)

    # Nao deveria chamar orb mesmo, mas mockamos por seguranca
    async def fake_run_orb(*args, **kwargs):  # pragma: no cover
        raise AssertionError("orb nao deve ser chamado")

    monkeypatch.setattr(lab, "_run_orb", fake_run_orb)

    token = await _login(client, admin_user)
    for bad in ["evil; rm -rf /", "../etc/passwd", "lab-", "not-lab-prefix"]:
        r = await client.post(
            f"/api/v1/lab/vms/{bad}/start",
            headers={"Authorization": f"Bearer {token}"},
        )
        # FastAPI quebra path em "/" — alguns retornam 404 do roteador,
        # outros 400 da validacao. Os dois sao bloqueio valido.
        assert r.status_code in (400, 404), f"esperava 400/404 pra {bad!r}, deu {r.status_code}"


@pytest.mark.asyncio
async def test_start_vm_ok(
    client: AsyncClient, admin_user: User, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_lab_mode(monkeypatch)

    calls: list[tuple] = []

    async def fake_run_orb(*args: str, timeout: int = 30):  # noqa: ASYNC109
        calls.append(args)
        return (0, "", "")

    monkeypatch.setattr(lab, "_run_orb", fake_run_orb)

    token = await _login(client, admin_user)
    r = await client.post(
        "/api/v1/lab/vms/lab-debian-11/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body == {"name": "lab-debian-11", "action": "start", "ok": True, "detail": ""}
    assert calls == [("start", "lab-debian-11")]


# Reset — apaga alerts/actions, NAO apaga hosts/audit_logs


@pytest.mark.asyncio
async def test_reset_deletes_alerts_and_actions_keeps_hosts_and_audit(
    client: AsyncClient, admin_user: User, db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_lab_mode(monkeypatch)

    # Seed: 1 host + 2 alerts + 1 action
    host = Host(
        org_id=admin_user.org_id, name="lab-debian-11",
        hostname="lab-debian-11.orb.local", status="active",
    )
    db_session.add(host)
    await db_session.flush()
    now = dt.datetime.now(dt.UTC)
    db_session.add_all([
        Alert(
            host_id=host.id, rule_id="r1", rule_name="r1", severity="high",
            description="x", count=1, first_event_at=now, last_event_at=now,
            status="open", context={}, dedup_key="k1",
        ),
        Alert(
            host_id=host.id, rule_id="r2", rule_name="r2", severity="medium",
            description="y", count=1, first_event_at=now, last_event_at=now,
            status="open", context={}, dedup_key="k2",
        ),
        Action(
            host_id=host.id, action_type="block_ip", target="203.0.113.1",
            status="pending", reason="brute_force",
        ),
    ])
    await db_session.commit()

    # Conta audit_logs antes pra confirmar que nao mexemos
    audit_before = (await db_session.execute(
        AuditLog.__table__.select().with_only_columns(AuditLog.id)
    )).scalars().all()
    audit_count_before = len(list(audit_before))

    token = await _login(client, admin_user)
    r = await client.post(
        "/api/v1/lab/reset",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["alerts_deleted"] == 2
    assert body["actions_deleted"] == 1

    # Host ainda existe
    assert await db_session.get(Host, host.id) is not None
    # Alerts e actions sumiram
    remaining_alerts = (await db_session.execute(
        Alert.__table__.select().where(Alert.host_id == host.id)
    )).all()
    assert remaining_alerts == []
    # Audit cresceu (novo log de lab_demo_reset), nao diminuiu
    audit_after = (await db_session.execute(
        AuditLog.__table__.select().with_only_columns(AuditLog.id)
    )).scalars().all()
    assert len(list(audit_after)) > audit_count_before
