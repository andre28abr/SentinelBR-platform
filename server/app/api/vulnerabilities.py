"""REST endpoints de inventario e vulnerabilidades por host."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import case, select

from app.api.deps import CurrentUser, DbSession, OperatorUser
from app.models import Host, HostPackage, HostVulnerability
from app.schemas.vulnerability import (
    HostPackageResponse,
    HostVulnerabilityResponse,
    HostVulnerabilitySummary,
)
from app.services.vuln_scan import compute_risk_score, scan_host

router = APIRouter(prefix="/api/v1/hosts", tags=["vulnerabilities"])


@router.get("/{host_id}/packages", response_model=list[HostPackageResponse])
async def list_packages(
    host_id: uuid.UUID,
    db: DbSession,
    current: CurrentUser,
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[HostPackage]:
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    result = await db.execute(
        select(HostPackage)
        .where(HostPackage.host_id == host_id)
        .order_by(HostPackage.name)
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{host_id}/vulnerabilities", response_model=HostVulnerabilitySummary)
async def list_vulnerabilities(
    host_id: uuid.UUID, db: DbSession, current: CurrentUser
) -> HostVulnerabilitySummary:
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")

    severity_order = case(
        (HostVulnerability.severity == "critical", 1),
        (HostVulnerability.severity == "high", 2),
        (HostVulnerability.severity == "medium", 3),
        (HostVulnerability.severity == "low", 4),
        else_=5,
    )
    items = (
        await db.execute(
            select(HostVulnerability)
            .where(HostVulnerability.host_id == host_id)
            .order_by(severity_order, HostVulnerability.cvss_score.desc())
        )
    ).scalars().all()

    by_severity: dict[str, int] = {}
    for v in items:
        by_severity[v.severity] = by_severity.get(v.severity, 0) + 1

    last_scan = max((v.last_seen_at for v in items), default=None)

    return HostVulnerabilitySummary(
        score=compute_risk_score([v.severity for v in items]),
        by_severity=by_severity,
        total=len(items),
        last_scan_at=last_scan,
        items=[HostVulnerabilityResponse.model_validate(v) for v in items],
    )


@router.post("/{host_id}/scan", status_code=202)
async def trigger_scan(host_id: uuid.UUID, db: DbSession, current: OperatorUser) -> dict:
    """Dispara scan manual (mesmo task que roda apos SubmitInventory).

    NB: chamada inline (await) — para hosts grandes, considerar mover pra
    Celery delay() em fase futura (vide auditoria Fase 3).
    """
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")

    summary = await scan_host(host_id)
    return summary
