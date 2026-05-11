"""REST endpoints de alertas — listagem, ack, resolve."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Alert
from app.schemas.alert import AlertResponse, AlertUpdate
from app.services import audit

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    db: DbSession,
    _: CurrentUser,
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    host_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Alert]:
    stmt = select(Alert).order_by(Alert.last_event_at.desc()).limit(limit)
    if status_filter:
        stmt = stmt.where(Alert.status == status_filter)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if host_id:
        stmt = stmt.where(Alert.host_id == host_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/count", response_model=dict)
async def count_alerts(db: DbSession, _: CurrentUser) -> dict[str, int]:
    """Counters pra badge no header. Retorna {open, total}."""
    open_count = await db.scalar(
        select(func.count()).select_from(Alert).where(Alert.status == "open")
    )
    total = await db.scalar(select(func.count()).select_from(Alert))
    return {"open": open_count or 0, "total": total or 0}


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: uuid.UUID, db: DbSession, _: CurrentUser) -> Alert:
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta nao encontrado")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: uuid.UUID,
    payload: AlertUpdate,
    request: Request,
    db: DbSession,
    current: CurrentUser,
) -> Alert:
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta nao encontrado")
    old_status = alert.status
    alert.status = payload.status

    action_name = (
        "alert_acknowledged" if payload.status == "acknowledged"
        else "alert_resolved" if payload.status == "resolved"
        else "alert_status_changed"
    )
    await audit.log_action(
        db, action=action_name, actor=current, request=request,
        target_type="alert", target_id=alert_id,
        details={"old_status": old_status, "new_status": payload.status,
                 "rule_id": alert.rule_id},
    )
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: uuid.UUID, db: DbSession, _: CurrentUser) -> None:
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta nao encontrado")
    await db.delete(alert)
    await db.commit()
