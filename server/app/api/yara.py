"""REST endpoints YARA — dispara scan manual e quarentena via Action."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Action, Host
from app.schemas.action import ActionResponse
from app.services import audit

router = APIRouter(prefix="/api/v1/hosts", tags=["yara"])


class YaraScanRequest(BaseModel):
    path: str = Field(min_length=1, max_length=512, description="diretorio ou arquivo a escanear")
    reason: str = Field(default="manual_ui", max_length=100)


@router.post(
    "/{host_id}/yara-scan",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_yara_scan(
    host_id: uuid.UUID,
    payload: YaraScanRequest,
    request: Request,
    db: DbSession,
    current: CurrentUser,
) -> Action:
    """Cria uma Action 'run_yara_scan' que sera enviada ao agente no proximo heartbeat."""
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")

    # Idempotencia: nao cria 2 scans 'pending' pro mesmo path no mesmo host.
    existing = await db.execute(
        select(Action.id).where(
            Action.host_id == host_id,
            Action.action_type == "run_yara_scan",
            Action.target == payload.path,
            Action.status.in_(("pending", "sent")),
        )
    )
    if existing.first() is not None:
        raise HTTPException(
            status_code=409,
            detail="ja existe scan pendente desse path nesse host",
        )

    action = Action(
        host_id=host_id,
        action_type="run_yara_scan",
        target=payload.path,
        reason=payload.reason,
        status="pending",
    )
    db.add(action)
    await db.flush()

    await audit.log_action(
        db, action="yara_scan_triggered", actor=current, request=request,
        target_type="host", target_id=host_id,
        details={"path": payload.path, "reason": payload.reason, "action_id": str(action.id)},
    )
    await db.commit()
    await db.refresh(action)
    return action
