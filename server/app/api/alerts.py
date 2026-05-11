"""REST endpoints de alertas — listagem, ack, resolve."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Alert
from app.schemas.alert import AlertResponse, AlertUpdate

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
    db: DbSession,
    _: CurrentUser,
) -> Alert:
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alerta nao encontrado")
    alert.status = payload.status
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
