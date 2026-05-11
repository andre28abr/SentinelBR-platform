import pytest
from httpx import AsyncClient

from app.models import User


@pytest.mark.asyncio
async def test_login_returns_tokens(client: AsyncClient, admin_user: User) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client: AsyncClient, admin_user: User) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "errada"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_with_matching_org_slug_succeeds(
    client: AsyncClient, admin_user: User,
) -> None:
    """admin_user pertence a org slug 'test' (do conftest)."""
    r = await client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_user.email,
            "password": "teste1234",
            "org_slug": "test",
        },
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_org_slug_fails(
    client: AsyncClient, admin_user: User,
) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        json={
            "email": admin_user.email,
            "password": "teste1234",
            "org_slug": "outra-org-qualquer",
        },
    )
    assert r.status_code == 401
    assert "organizacao" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient) -> None:
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, admin_user: User) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "teste1234"},
    )
    token = login.json()["access_token"]
    r = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == admin_user.email
    assert body["role"] == "admin"
