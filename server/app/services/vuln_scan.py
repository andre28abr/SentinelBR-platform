"""Servico de scan de vulnerabilidades: cross-ref host_packages com OSV
e popula host_vulnerabilities.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models import Host, HostPackage, HostVulnerability
from app.services import osv

log = logging.getLogger(__name__)


# Pesos pra calcular score de risco 0-100. Score = min(100, sum(peso por sev)).
_SEV_WEIGHT = {
    "critical": 15.0,
    "high": 6.0,
    "medium": 2.0,
    "low": 0.5,
    "unknown": 0.5,
}


def compute_risk_score(severities: list[str]) -> int:
    if not severities:
        return 0
    total = sum(_SEV_WEIGHT.get(s, 0.5) for s in severities)
    return min(100, int(round(total)))


async def scan_host(host_id: uuid.UUID) -> dict:
    """Scan um host: query OSV pra cada pacote instalado, atualiza host_vulnerabilities.

    Retorna sumario {scanned: N, found: M, by_severity: {...}, score: X}.
    """
    async with SessionLocal() as db:
        host = await db.get(Host, host_id)
        if host is None:
            return {"error": "host nao encontrado", "scanned": 0, "found": 0}

        ecosystem = osv.os_to_ecosystem(host.os_distro, host.os_version)
        if ecosystem is None:
            log.info(
                "scan: ecosystem nao mapeado pra distro=%s version=%s — pulando",
                host.os_distro, host.os_version,
            )
            return {"error": "ecosystem nao mapeado", "scanned": 0, "found": 0}

        packages = (
            await db.execute(
                select(HostPackage).where(HostPackage.host_id == host_id)
            )
        ).scalars().all()
        if not packages:
            return {"scanned": 0, "found": 0, "by_severity": {}, "score": 0}

        queries = [
            osv.PackageQuery(name=p.name, version=p.version, ecosystem=ecosystem)
            for p in packages
        ]

        try:
            vulns_by_pkg = await osv.query_batch(queries)
        except Exception as e:  # noqa: BLE001
            log.warning("OSV scan falhou: %s", e)
            return {"error": str(e), "scanned": len(packages), "found": 0}

        return await _persist_results(db, host_id, packages, vulns_by_pkg)


async def _persist_results(
    db: AsyncSession,
    host_id: uuid.UUID,
    packages: list[HostPackage],
    vulns_by_pkg: dict[str, list[osv.Vulnerability]],
) -> dict:
    pkg_versions = {p.name: p.version for p in packages}

    # Estrategia: deleta tudo e re-insere (pacotes patcheados saem, novos entram).
    await db.execute(delete(HostVulnerability).where(HostVulnerability.host_id == host_id))

    severities: list[str] = []
    inserted = 0
    seen_keys: set[tuple[str, str]] = set()  # (cve_id, package_name) pra dedup
    for pkg_name, vulns in vulns_by_pkg.items():
        installed = pkg_versions.get(pkg_name, "")
        for v in vulns:
            key = (v.cve_id, pkg_name)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            db.add(HostVulnerability(
                host_id=host_id,
                cve_id=v.cve_id,
                package_name=pkg_name,
                installed_version=installed,
                fixed_version=v.fixed_version,
                severity=v.severity,
                cvss_score=v.cvss_score,
                summary=v.summary,
                references=v.references[:5] if v.references else None,
                discovered_at=dt.datetime.now(dt.UTC),
            ))
            severities.append(v.severity)
            inserted += 1

    await db.commit()

    by_severity: dict[str, int] = {}
    for s in severities:
        by_severity[s] = by_severity.get(s, 0) + 1

    return {
        "scanned": len(packages),
        "found": inserted,
        "by_severity": by_severity,
        "score": compute_risk_score(severities),
    }
