import pytest
from httpx import AsyncClient

from app.models import User


async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_hosts_list_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/hosts")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_host(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/api/v1/hosts",
        json={"name": "srv1", "hostname": "srv1.example.com"},
        headers=headers,
    )
    assert r.status_code == 201
    created = r.json()
    assert created["name"] == "srv1"
    assert created["status"] == "pending"

    r = await client.get("/api/v1/hosts", headers=headers)
    assert r.status_code == 200
    listed = r.json()
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_404_for_unknown_host(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/hosts/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404
