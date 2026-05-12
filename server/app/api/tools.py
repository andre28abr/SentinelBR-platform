"""REST endpoints rkhunter + lynis — dispara scans/audits via Action."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import DbSession, OperatorUser
from app.models import Action, Host
from app.schemas.action import ActionResponse
from app.services import audit

router = APIRouter(prefix="/api/v1/hosts", tags=["tools"])


class ToolRunRequest(BaseModel):
    reason: str = Field(default="manual_ui", max_length=255)


async def _create_tool_action(
    db,
    host_id: uuid.UUID,
    action_type: str,
    require_field: str,
    payload: ToolRunRequest,
    request: Request,
    current,
) -> Action:
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    if not getattr(host, require_field):
        raise HTTPException(
            status_code=400,
            detail=f"'{require_field}' nao reportado pelo agente nesse host",
        )

    # Idempotencia: 1 scan/audit pending por vez por host.
    existing = await db.execute(
        select(Action.id).where(
            Action.host_id == host_id,
            Action.action_type == action_type,
            Action.status.in_(("pending", "sent")),
        )
    )
    if existing.first() is not None:
        raise HTTPException(
            status_code=409,
            detail=f"ja existe '{action_type}' pendente nesse host",
        )

    action = Action(
        host_id=host_id,
        action_type=action_type,
        target=action_type,  # nao tem alvo especifico; usa o tipo como label
        reason=payload.reason,
        status="pending",
    )
    db.add(action)
    await db.flush()

    await audit.log_action(
        db, action=f"{action_type}_triggered", actor=current, request=request,
        target_type="host", target_id=host_id,
        details={"reason": payload.reason, "action_id": str(action.id)},
    )
    await db.commit()
    await db.refresh(action)
    return action


@router.post(
    "/{host_id}/rkhunter-scan",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_rkhunter_scan(
    host_id: uuid.UUID,
    payload: ToolRunRequest,
    request: Request,
    db: DbSession,
    current: OperatorUser,
) -> Action:
    """Roda 'rkhunter --check --sk' no host. Saida vira eventos."""
    return await _create_tool_action(
        db, host_id, "run_rkhunter_scan", "rkhunter_installed",
        payload, request, current,
    )


@router.post(
    "/{host_id}/lynis-audit",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_lynis_audit(
    host_id: uuid.UUID,
    payload: ToolRunRequest,
    request: Request,
    db: DbSession,
    current: OperatorUser,
) -> Action:
    """Roda 'lynis audit system --quick' no host. Saida vira eventos."""
    return await _create_tool_action(
        db, host_id, "run_lynis_audit", "lynis_installed",
        payload, request, current,
    )


@router.post(
    "/{host_id}/chkrootkit-scan",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_chkrootkit_scan(
    host_id: uuid.UUID,
    payload: ToolRunRequest,
    request: Request,
    db: DbSession,
    current: OperatorUser,
) -> Action:
    """Roda 'chkrootkit -q' no host. Warnings viram eventos."""
    return await _create_tool_action(
        db, host_id, "run_chkrootkit_scan", "chkrootkit_installed",
        payload, request, current,
    )


@router.post(
    "/{host_id}/aide-check",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_aide_check(
    host_id: uuid.UUID,
    payload: ToolRunRequest,
    request: Request,
    db: DbSession,
    current: OperatorUser,
) -> Action:
    """Roda 'aide --check' no host (precisa --init feito antes)."""
    return await _create_tool_action(
        db, host_id, "run_aide_check", "aide_installed",
        payload, request, current,
    )
