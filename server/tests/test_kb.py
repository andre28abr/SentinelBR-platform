"""Testes da Knowledge Base — loader + REST endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models import User
from app.services import kb


async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


def test_kb_loader_techniques() -> None:
    techs = kb.list_techniques()
    assert len(techs) >= 5
    # Schema basico esperado por cada YAML
    for t in techs:
        assert "id" in t
        assert "name" in t
        assert "tactic" in t
        assert "severity" in t
        assert "description" in t


def test_kb_loader_hunting() -> None:
    queries = kb.list_hunting_queries()
    assert len(queries) >= 3
    for q in queries:
        assert "id" in q
        assert "name" in q
        assert "description" in q


def test_kb_loader_playbooks() -> None:
    plays = kb.list_playbooks()
    assert len(plays) >= 2
    for p in plays:
        assert "id" in p
        assert "name" in p
        assert "how_to_run" in p


def test_kb_get_technique_by_id() -> None:
    t = kb.get_technique("T1110.001")
    assert t is not None
    assert "Brute Force" in t["name"]


def test_kb_get_technique_unknown() -> None:
    assert kb.get_technique("T9999") is None


@pytest.mark.asyncio
async def test_endpoint_list_techniques_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/kb/techniques")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_list_techniques(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/kb/techniques",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    techs = r.json()
    assert isinstance(techs, list)
    assert len(techs) >= 5
    assert all("id" in t for t in techs)


@pytest.mark.asyncio
async def test_endpoint_get_technique(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/kb/techniques/T1110.001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    t = r.json()
    assert t["id"] == "T1110.001"


@pytest.mark.asyncio
async def test_endpoint_get_technique_404(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/kb/techniques/T9999.999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_hunting(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/kb/hunting",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) >= 3


@pytest.mark.asyncio
async def test_endpoint_playbooks(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/kb/playbooks",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) >= 2
