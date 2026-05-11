"""Testes do scan de vulnerabilidades + endpoints + OSV mapping (sem rede)."""

from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Host, HostPackage, HostVulnerability, User
from app.services import osv
from app.services.vuln_scan import compute_risk_score

# ─── OSV mapping (puro) ───────────────────────────────────────────────────────

def test_osv_ecosystem_debian() -> None:
    assert osv.os_to_ecosystem("debian", "12") == "Debian:12"
    assert osv.os_to_ecosystem("debian", "12.5") == "Debian:12"  # major only


def test_osv_ecosystem_ubuntu() -> None:
    assert osv.os_to_ecosystem("ubuntu", "22.04") == "Ubuntu:22.04"


def test_osv_ecosystem_rocky() -> None:
    assert osv.os_to_ecosystem("rocky", "9.3") == "Rocky Linux:9"


def test_osv_ecosystem_alpine() -> None:
    assert osv.os_to_ecosystem("alpine", "3.19") == "Alpine:v3.19"


def test_osv_ecosystem_unknown_returns_none() -> None:
    assert osv.os_to_ecosystem("haiku", "1") is None
    assert osv.os_to_ecosystem(None, "1") is None


# ─── Risk score ───────────────────────────────────────────────────────────────

def test_score_empty_is_zero() -> None:
    assert compute_risk_score([]) == 0


def test_score_single_critical() -> None:
    assert compute_risk_score(["critical"]) == 15


def test_score_capped_at_100() -> None:
    # 10 criticas -> 150 -> cap em 100
    assert compute_risk_score(["critical"] * 10) == 100


def test_score_mixed() -> None:
    # 1 high (6) + 2 medium (4) + 3 low (1.5) = 11.5 -> 12
    assert compute_risk_score(["high", "medium", "medium", "low", "low", "low"]) == 12


# ─── Endpoints ────────────────────────────────────────────────────────────────

async def _login(client: AsyncClient, user: User) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "teste1234"},
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
async def test_packages_endpoint_404(client: AsyncClient, admin_user: User) -> None:
    token = await _login(client, admin_user)
    r = await client.get(
        "/api/v1/hosts/00000000-0000-0000-0000-000000000000/packages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_packages_endpoint_lists_seeded(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = Host(name="vh", hostname="vh.example.com", status="active")
    db_session.add(host)
    await db_session.commit()
    await db_session.refresh(host)

    db_session.add(HostPackage(host_id=host.id, name="openssl", version="1.1.1n", source="apt"))
    db_session.add(HostPackage(host_id=host.id, name="sudo", version="1.9.13", source="apt"))
    await db_session.commit()

    token = await _login(client, admin_user)
    r = await client.get(
        f"/api/v1/hosts/{host.id}/packages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    names = sorted(p["name"] for p in body)
    assert names == ["openssl", "sudo"]


@pytest.mark.asyncio
async def test_vulnerabilities_summary_with_seeded_data(
    client: AsyncClient, admin_user: User, db_session: AsyncSession
) -> None:
    host = Host(name="vh2", hostname="vh2.example.com", status="active")
    db_session.add(host)
    await db_session.commit()
    await db_session.refresh(host)

    now = dt.datetime.now(dt.UTC)
    db_session.add(HostVulnerability(
        host_id=host.id, cve_id="CVE-2024-1111", package_name="openssl",
        installed_version="1.1.1n", fixed_version="1.1.1w",
        severity="critical", cvss_score=9.8, summary="x",
        discovered_at=now, last_seen_at=now,
    ))
    db_session.add(HostVulnerability(
        host_id=host.id, cve_id="CVE-2024-2222", package_name="sudo",
        installed_version="1.9.13", fixed_version=None,
        severity="medium", cvss_score=5.5, summary="y",
        discovered_at=now, last_seen_at=now,
    ))
    await db_session.commit()

    token = await _login(client, admin_user)
    r = await client.get(
        f"/api/v1/hosts/{host.id}/vulnerabilities",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert body["by_severity"]["critical"] == 1
    assert body["by_severity"]["medium"] == 1
    # 15 (critical) + 2 (medium) = 17
    assert body["score"] == 17
    # primeira deve ser a mais severa (critical)
    assert body["items"][0]["severity"] == "critical"


@pytest.mark.asyncio
async def test_vulnerabilities_endpoint_requires_auth(client: AsyncClient) -> None:
    r = await client.get("/api/v1/hosts/00000000-0000-0000-0000-000000000000/vulnerabilities")
    assert r.status_code == 401


# ─── OSV normalization (mocked) ───────────────────────────────────────────────

def test_normalize_vuln_picks_cve_alias() -> None:
    raw = {
        "id": "GHSA-xxxx-yyyy-zzzz",
        "aliases": ["CVE-2024-99999"],
        "summary": "test vuln",
        "affected": [{"ranges": [{"events": [{"introduced": "0"}, {"fixed": "1.2.3"}]}]}],
        "references": [{"url": "https://example.com/advisory"}],
    }
    v = osv._normalize_vuln(raw)
    assert v.cve_id == "CVE-2024-99999"
    assert v.fixed_version == "1.2.3"
    assert "https://example.com/advisory" in v.references


def test_normalize_vuln_falls_back_to_id_if_no_cve_alias() -> None:
    raw = {"id": "GHSA-foo", "aliases": ["MAVEN:x"], "summary": "x"}
    v = osv._normalize_vuln(raw)
    assert v.cve_id == "GHSA-foo"
