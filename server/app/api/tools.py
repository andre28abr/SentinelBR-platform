"""REST endpoints rkhunter + chkrootkit + lynis + AIDE — scans via Action."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import DbSession, OperatorUser
from app.models import Action
from app.schemas.action import ActionResponse
from app.services.actions import create_pending_action, get_host_in_org_or_404

router = APIRouter(prefix="/api/v1/hosts", tags=["tools"])


class ToolRunRequest(BaseModel):
    reason: str = Field(default="manual_ui", max_length=255)


async def _trigger_tool(
    db,
    host_id: uuid.UUID,
    action_type: str,
    require_field: str,
    payload: ToolRunRequest,
    request: Request,
    current,
) -> Action:
    host = await get_host_in_org_or_404(db, host_id, current.org_id)
    if not getattr(host, require_field):
        raise HTTPException(
            status_code=400,
            detail=f"'{require_field}' nao reportado pelo agente nesse host",
        )
    return await create_pending_action(
        db,
        host=host,
        actor=current,
        request=request,
        action_type=action_type,
        target=action_type,  # 1 desses por vez por host (sem alvo especifico)
        reason=payload.reason,
        audit_action=f"{action_type}_triggered",
        audit_details={"reason": payload.reason},
        idempotency_check_target=False,
        conflict_detail=f"ja existe '{action_type}' pendente nesse host",
    )


@router.post(
    "/{host_id}/rkhunter-scan",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_rkhunter_scan(
    host_id: uuid.UUID, payload: ToolRunRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Roda 'rkhunter --check --sk' no host. Saida vira eventos."""
    return await _trigger_tool(
        db, host_id, "run_rkhunter_scan", "rkhunter_installed",
        payload, request, current,
    )


@router.post(
    "/{host_id}/lynis-audit",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_lynis_audit(
    host_id: uuid.UUID, payload: ToolRunRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Roda 'lynis audit system --quick' no host. Saida vira eventos."""
    return await _trigger_tool(
        db, host_id, "run_lynis_audit", "lynis_installed",
        payload, request, current,
    )


@router.post(
    "/{host_id}/chkrootkit-scan",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_chkrootkit_scan(
    host_id: uuid.UUID, payload: ToolRunRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Roda 'chkrootkit -q' no host. Warnings viram eventos."""
    return await _trigger_tool(
        db, host_id, "run_chkrootkit_scan", "chkrootkit_installed",
        payload, request, current,
    )


@router.post(
    "/{host_id}/aide-check",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_aide_check(
    host_id: uuid.UUID, payload: ToolRunRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Roda 'aide --check' no host (precisa --init feito antes)."""
    return await _trigger_tool(
        db, host_id, "run_aide_check", "aide_installed",
        payload, request, current,
    )
