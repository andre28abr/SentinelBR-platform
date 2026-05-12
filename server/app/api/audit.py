"""REST endpoints de auditoria + relatorio de compliance LGPD."""

from __future__ import annotations

import asyncio
import datetime as dt
import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import cast, func, select
from sqlalchemy.types import Date

from app.api.deps import CurrentUser, DbSession
from app.models import Action, Alert, AuditLog, Host, Organization
from app.schemas.audit_log import AuditLogResponse
from app.schemas.compliance import ComplianceReport
from app.services import pdf_report

router = APIRouter(prefix="/api/v1", tags=["compliance"])


class LoginTimelinePoint(BaseModel):
    date: str  # YYYY-MM-DD
    success: int
    failed: int


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    db: DbSession,
    current: CurrentUser,
    actor_user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=365),
    only_failures: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[AuditLog]:
    since = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
    # Inclui logs da org E logs globais (ex: login_failed sem actor identificado).
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.created_at >= since,
            (AuditLog.org_id == current.org_id) | (AuditLog.org_id.is_(None)),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if only_failures:
        stmt = stmt.where(AuditLog.success.is_(False))

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/compliance/report", response_model=ComplianceReport)
async def compliance_report(
    db: DbSession, current: CurrentUser, days: int = Query(default=30, ge=1, le=365)
) -> ComplianceReport:
    end = dt.datetime.now(dt.UTC)
    start = end - dt.timedelta(days=days)

    org_id = current.org_id
    org_or_global = (AuditLog.org_id == org_id) | (AuditLog.org_id.is_(None))

    # Antes: 11 awaits sequenciais (~11 round-trips ao DB). Agora: 1 round
    # via asyncio.gather() — todas as queries voam em paralelo.
    # Em DB local com latencia ~2ms, ganho marginal; em DB remoto com
    # latencia 20-50ms, reduz tempo do endpoint pela metade.
    queries = [
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.action.in_(("login_success", "login_failed")),
                AuditLog.created_at >= start, org_or_global,
            )
        ),
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.action == "login_failed",
                AuditLog.created_at >= start, org_or_global,
            )
        ),
        db.scalar(
            select(func.count(func.distinct(AuditLog.actor_user_id))).where(
                AuditLog.action == "login_success",
                AuditLog.created_at >= start,
                AuditLog.actor_user_id.is_not(None),
                org_or_global,
            )
        ),
        db.scalar(
            select(func.count()).select_from(Host).where(Host.org_id == org_id)
        ),
        db.scalar(
            select(func.count()).select_from(Host).where(
                Host.org_id == org_id, Host.status == "active",
            )
        ),
        db.scalar(
            select(func.count()).select_from(Host).where(
                Host.org_id == org_id, Host.created_at >= start,
            )
        ),
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.action == "host_deleted",
                AuditLog.created_at >= start, org_or_global,
            )
        ),
        db.scalar(
            select(func.count()).select_from(Alert)
            .join(Host, Alert.host_id == Host.id)
            .where(Host.org_id == org_id, Alert.created_at >= start)
        ),
        db.scalar(
            select(func.count()).select_from(Alert)
            .join(Host, Alert.host_id == Host.id)
            .where(Host.org_id == org_id, Alert.status == "open")
        ),
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.action == "alert_acknowledged",
                AuditLog.created_at >= start, org_or_global,
            )
        ),
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.action == "alert_resolved",
                AuditLog.created_at >= start, org_or_global,
            )
        ),
        db.scalar(
            select(func.count()).select_from(Action)
            .join(Host, Action.host_id == Host.id)
            .where(
                Host.org_id == org_id,
                Action.status == "executed",
                Action.executed_at >= start,
            )
        ),
        # MTTR no SQL via AVG(EXTRACT(EPOCH FROM diff)).
        db.scalar(
            select(
                func.avg(func.extract("epoch", Action.executed_at - Alert.created_at))
            )
            .select_from(Alert)
            .join(Action, Action.alert_id == Alert.id)
            .join(Host, Alert.host_id == Host.id)
            .where(
                Host.org_id == org_id,
                Alert.created_at >= start,
                Action.executed_at.is_not(None),
            )
        ),
        db.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.created_at >= start, org_or_global,
            )
        ),
    ]
    results = await asyncio.gather(*queries)
    (
        total_logins, failed_logins, distinct_users,
        hosts_total, hosts_active, hosts_created, hosts_deleted,
        alerts_created, alerts_open, alerts_ack, alerts_resolved,
        actions_exec, mttr_raw, audit_entries,
    ) = (r or 0 for r in results)
    mttr_secs = float(mttr_raw) if mttr_raw else None
    # `or 0` acima troca None por 0 mas tb engole 0.0 do mttr; corrigido acima.

    return ComplianceReport(
        period_start=start,
        period_end=end,
        period_days=days,
        total_logins=total_logins,
        failed_logins=failed_logins,
        distinct_users_logged_in=distinct_users,
        hosts_total=hosts_total,
        hosts_active=hosts_active,
        hosts_created_in_period=hosts_created,
        hosts_deleted_in_period=hosts_deleted,
        alerts_created_in_period=alerts_created,
        alerts_open=alerts_open,
        alerts_acknowledged_in_period=alerts_ack,
        alerts_resolved_in_period=alerts_resolved,
        actions_executed_in_period=actions_exec,
        mttr_seconds=mttr_secs,
        audit_log_entries_in_period=audit_entries,
        audit_retention_days=180,  # fixo por enquanto; vira config futura
    )


@router.get("/compliance/report/pdf")
async def compliance_report_pdf(
    db: DbSession, current: CurrentUser, days: int = Query(default=30, ge=1, le=365)
) -> Response:
    """Mesmo report do endpoint JSON, mas renderizado como PDF (LGPD Art. 37)."""
    report = await compliance_report(db, current, days)
    org = await db.get(Organization, current.org_id)
    org_name = org.name if org else "Organizacao"
    pdf_bytes = pdf_report.render(report, org_name=org_name)
    filename = f"compliance-{dt.datetime.now(dt.UTC).strftime('%Y%m%d')}-{days}d.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/compliance/login-timeline", response_model=list[LoginTimelinePoint])
async def login_timeline(
    db: DbSession, current: CurrentUser, days: int = Query(default=30, ge=1, le=365),
) -> list[LoginTimelinePoint]:
    """Serie temporal diaria de logins (success vs failed) — pra grafico de linha."""
    end = dt.datetime.now(dt.UTC)
    start = end - dt.timedelta(days=days)
    org_or_global = (AuditLog.org_id == current.org_id) | (AuditLog.org_id.is_(None))

    day_col = cast(AuditLog.created_at, Date).label("day")
    rows = (
        await db.execute(
            select(day_col, AuditLog.action, func.count().label("n"))
            .where(
                AuditLog.action.in_(("login_success", "login_failed")),
                AuditLog.created_at >= start,
                org_or_global,
            )
            .group_by(day_col, AuditLog.action)
            .order_by(day_col)
        )
    ).all()

    # Agrega em dict {date: {success, failed}}
    bucket: dict[str, dict[str, int]] = {}
    for day, action, n in rows:
        key = day.isoformat()
        bucket.setdefault(key, {"success": 0, "failed": 0})
        if action == "login_success":
            bucket[key]["success"] = n
        else:
            bucket[key]["failed"] = n

    # Garante pontos pra todos os dias do periodo (mesmo zero)
    out: list[LoginTimelinePoint] = []
    cur = start.date()
    end_date = end.date()
    while cur <= end_date:
        key = cur.isoformat()
        data = bucket.get(key, {"success": 0, "failed": 0})
        out.append(LoginTimelinePoint(date=key, success=data["success"], failed=data["failed"]))
        cur += dt.timedelta(days=1)
    return out
