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
async def test_mint_token_requires_auth(client: AsyncClient) -> None:
    r = await client.post("/api/v1/hosts/00000000-0000-0000-0000-000000000000/enrollment-token")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_mint_token_404_for_unknown_host(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.post(
        "/api/v1/hosts/00000000-0000-0000-0000-000000000000/enrollment-token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_full_enrollment_flow(client: AsyncClient, admin_user: User) -> None:
    auth = await _login(client, admin_user)
    headers = {"Authorization": f"Bearer {auth}"}

    create = await client.post(
        "/api/v1/hosts",
        json={"name": "h1", "hostname": "h1.example.com"},
        headers=headers,
    )
    assert create.status_code == 201
    host_id = create.json()["id"]

    mint = await client.post(f"/api/v1/hosts/{host_id}/enrollment-token", headers=headers)
    assert mint.status_code == 201
    body = mint.json()
    enrollment_token = body["token"]
    assert body["install_command"].startswith("sudo sentinel-agent enroll")
    assert enrollment_token in body["install_command"]

    enroll = await client.post(
        "/api/v1/agents/enroll",
        json={
            "token": enrollment_token,
            "hostname": "h1.example.com",
            "os": {
                "family": "redhat",
                "distro": "rocky",
                "version": "9.3",
                "arch": "amd64",
                "package_manager": "dnf",
                "firewall_tool": "firewalld",
                "mac_system": "selinux",
            },
        },
    )
    assert enroll.status_code == 200, enroll.text
    enroll_body = enroll.json()
    assert enroll_body["host_id"] == host_id
    assert "BEGIN CERTIFICATE" in enroll_body["ca_cert_pem"]
    assert "BEGIN CERTIFICATE" in enroll_body["client_cert_pem"]
    assert "BEGIN PRIVATE KEY" in enroll_body["client_key_pem"]

    # token e one-shot — segundo uso falha
    enroll2 = await client.post(
        "/api/v1/agents/enroll",
        json={
            "token": enrollment_token,
            "hostname": "h1.example.com",
            "os": {"family": "redhat", "distro": "rocky"},
        },
    )
    assert enroll2.status_code == 401

    # depois do enrollment, host esta active e tem os_distro populado
    after = await client.get(f"/api/v1/hosts/{host_id}", headers=headers)
    assert after.status_code == 200
    after_body = after.json()
    assert after_body["status"] == "active"
    assert after_body["os_distro"] == "rocky"
    assert after_body["os_family"] == "redhat"


@pytest.mark.asyncio
async def test_enroll_with_invalid_token(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/agents/enroll",
        json={
            "token": "token-que-nao-existe-em-lugar-nenhum",
            "hostname": "x",
            "os": {"family": "x", "distro": "x"},
        },
    )
    assert r.status_code == 401
