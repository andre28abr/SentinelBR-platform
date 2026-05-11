"""Testes do audit log + compliance report + PII masking."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User
from app.services import pii

# ─── PII masking (puro, sem fixtures) ─────────────────────────────────────────

def test_mask_email_simple() -> None:
    masked = pii.mask_email("contato user@empresa.com.br")
    # mascaramento preserva primeira letra + estrutura do email, mas obfusca o resto
    assert "user@" not in masked
    assert "empresa" not in masked
    assert "u***" in masked
    assert "e***" in masked


def test_mask_email_preserves_structure() -> None:
    masked = pii.mask_email("nome.sobrenome@gmail.com")
    assert masked != "nome.sobrenome@gmail.com"
    assert "@" in masked


def test_mask_ipv4_keeps_subnet() -> None:
    assert pii.mask_ipv4("from 203.0.113.42 port 22") == "from 203.0.113.x port 22"


def test_mask_cpf_full_redaction() -> None:
    assert pii.mask_cpf("CPF 123.456.789-00") == "CPF ***.***.***-**"


def test_mask_dict_recursive() -> None:
    raw = {
        "user.name": "alice@example.com",
        "source.ip": "1.2.3.4",
        "nested": {"cpf": "111.222.333-44"},
        "list": ["alice@x.com"],
    }
    out = pii.mask_dict(raw)
    assert "@" in out["user.name"] and "alice@example.com" not in out["user.name"]
    assert out["source.ip"] == "1.2.3.x"
    assert out["nested"]["cpf"] == "***.***.***-**"
    assert "alice@x.com" not in out["list"][0]


def test_mask_dict_preserves_keys_and_non_strings() -> None:
    raw = {"count": 42, "ok": True, "msg": "ip 1.2.3.4"}
    out = pii.mask_dict(raw)
    assert out["count"] == 42
    assert out["ok"] is True
    assert out["msg"] == "ip 1.2.3.x"


# ─── Audit + endpoints ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success_creates_audit(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    assert r.status_code == 200

    logs = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.action == "login_success")
        )
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].actor_user_id == admin_user.id
    assert logs[0].success is True


@pytest.mark.asyncio
async def test_login_failure_creates_audit(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "errada"},
    )
    assert r.status_code == 401

    logs = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.action == "login_failed")
        )
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].success is False


@pytest.mark.asyncio
async def test_host_created_logged(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    token = login.json()["access_token"]

    create = await client.post(
        "/api/v1/hosts",
        json={"name": "audit-host", "hostname": "audit.example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create.status_code == 201

    logs = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.action == "host_created")
        )
    ).scalars().all()
    assert len(logs) == 1
    assert logs[0].target_type == "host"
    assert logs[0].details.get("name") == "audit-host"


@pytest.mark.asyncio
async def test_audit_logs_endpoint_filters_by_action(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    token = login.json()["access_token"]

    r = await client.get(
        "/api/v1/audit-logs?action=login_success",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert all(e["action"] == "login_success" for e in body)


@pytest.mark.asyncio
async def test_compliance_report_returns_metrics(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    # gera um login pra ter algo no periodo
    await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    token = login.json()["access_token"]

    r = await client.get(
        "/api/v1/compliance/report?days=30",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["period_days"] == 30
    assert body["total_logins"] >= 2
    assert body["distinct_users_logged_in"] >= 1
    assert "audit_log_entries_in_period" in body
    assert "note" in body
