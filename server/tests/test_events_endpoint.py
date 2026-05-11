"""Test do REST GET /hosts/:id/events. Exige Loki disponivel pra fluxo completo."""

from __future__ import annotations

import httpx
import pytest
from httpx import AsyncClient

from app.models import User


async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


async def _loki_alive() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as cli:
            r = await cli.get("http://localhost:3100/ready")
            return r.status_code in (200, 503)
    except httpx.HTTPError:
        return False


@pytest.mark.asyncio
async def test_events_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/hosts/00000000-0000-0000-0000-000000000000/events")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_events_404_for_unknown_host(client: AsyncClient, admin_user: User) -> None:
    if not await _loki_alive():
        pytest.skip("Loki nao disponivel")
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/hosts/00000000-0000-0000-0000-000000000000/events",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_events_returns_empty_for_host_with_no_events(
    client: AsyncClient, admin_user: User
) -> None:
    if not await _loki_alive():
        pytest.skip("Loki nao disponivel")
    token = await _login(client, admin_user)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/hosts",
        json={"name": "host-sem-eventos", "hostname": "x.example.com"},
        headers=headers,
    )
    assert create.status_code == 201
    host_id = create.json()["id"]

    r = await client.get(f"/api/v1/hosts/{host_id}/events", headers=headers)
    assert r.status_code == 200
    assert r.json() == []
