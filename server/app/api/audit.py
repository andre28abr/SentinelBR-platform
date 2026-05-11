"""REST endpoints de auditoria + relatorio de compliance LGPD."""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Action, Alert, AuditLog, Host
from app.schemas.audit_log import AuditLogResponse
from app.schemas.compliance import ComplianceReport

router = APIRouter(prefix="/api/v1", tags=["compliance"])


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    db: DbSession,
    _: CurrentUser,
    actor_user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=365),
    only_failures: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[AuditLog]:
    since = dt.datetime.now(dt.UTC) - dt.timedelta(days=days)
    stmt = (
        select(AuditLog)
        .where(AuditLog.created_at >= since)
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
    db: DbSession, _: CurrentUser, days: int = Query(default=30, ge=1, le=365)
) -> ComplianceReport:
    end = dt.datetime.now(dt.UTC)
    start = end - dt.timedelta(days=days)

    # Auth metrics
    logins_q = select(func.count()).select_from(AuditLog).where(
        AuditLog.action.in_(("login_success", "login_failed")),
        AuditLog.created_at >= start,
    )
    total_logins = await db.scalar(logins_q) or 0

    failed_logins = await db.scalar(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "login_failed", AuditLog.created_at >= start,
        )
    ) or 0

    distinct_users = await db.scalar(
        select(func.count(func.distinct(AuditLog.actor_user_id))).where(
            AuditLog.action == "login_success",
            AuditLog.created_at >= start,
            AuditLog.actor_user_id.is_not(None),
        )
    ) or 0

    # Host metrics
    hosts_total = await db.scalar(select(func.count()).select_from(Host)) or 0
    hosts_active = await db.scalar(
        select(func.count()).select_from(Host).where(Host.status == "active")
    ) or 0
    hosts_created = await db.scalar(
        select(func.count()).select_from(Host).where(Host.created_at >= start)
    ) or 0
    hosts_deleted = await db.scalar(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "host_deleted", AuditLog.created_at >= start,
        )
    ) or 0

    # Detection metrics
    alerts_created = await db.scalar(
        select(func.count()).select_from(Alert).where(Alert.created_at >= start)
    ) or 0
    alerts_open = await db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == "open")
    ) or 0
    alerts_ack = await db.scalar(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "alert_acknowledged", AuditLog.created_at >= start,
        )
    ) or 0
    alerts_resolved = await db.scalar(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "alert_resolved", AuditLog.created_at >= start,
        )
    ) or 0
    actions_exec = await db.scalar(
        select(func.count()).select_from(Action).where(
            Action.status == "executed", Action.executed_at >= start,
        )
    ) or 0

    # MTTR: tempo medio entre Alert.created_at e Action.executed_at (vinculados por alert_id).
    mttr_secs: float | None = None
    join_rows = (
        await db.execute(
            select(Alert.created_at, Action.executed_at).join(
                Action, Action.alert_id == Alert.id, isouter=False
            ).where(
                Alert.created_at >= start,
                Action.executed_at.is_not(None),
            )
        )
    ).all()
    if join_rows:
        diffs = [(act - alr).total_seconds() for alr, act in join_rows]
        mttr_secs = sum(diffs) / len(diffs)

    audit_entries = await db.scalar(
        select(func.count()).select_from(AuditLog).where(AuditLog.created_at >= start)
    ) or 0

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
