"""REST endpoints de Actions — listagem por host + revert (unblock)."""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Action, Host
from app.schemas.action import ActionResponse, ActionUpdate
from app.services import audit

router = APIRouter(prefix="/api/v1", tags=["actions"])


async def _action_in_org_or_404(db, action_id: uuid.UUID, org_id: uuid.UUID) -> Action:
    action = await db.get(Action, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="acao nao encontrada")
    host = await db.get(Host, action.host_id)
    if host is None or host.org_id != org_id:
        raise HTTPException(status_code=404, detail="acao nao encontrada")
    return action


@router.get("/hosts/{host_id}/actions", response_model=list[ActionResponse])
async def list_actions_for_host(
    host_id: uuid.UUID, db: DbSession, current: CurrentUser
) -> list[Action]:
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    result = await db.execute(
        select(Action).where(Action.host_id == host_id).order_by(Action.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/actions/{action_id}", response_model=ActionResponse)
async def revert_action(
    action_id: uuid.UUID, payload: ActionUpdate, request: Request,
    db: DbSession, current: CurrentUser,
) -> Action:
    action = await _action_in_org_or_404(db, action_id, current.org_id)

    if payload.status != "reverted":
        raise HTTPException(status_code=400, detail="status invalido")

    if action.action_type == "block_ip" and action.status == "executed":
        # cria uma action 'unblock_ip' pra ser enviada no proximo heartbeat
        unblock = Action(
            host_id=action.host_id,
            action_type="unblock_ip",
            target=action.target,
            reason=f"revert:{action.id}",
            status="pending",
        )
        db.add(unblock)
        action.status = "reverted"
        action.reverted_at = dt.datetime.now(dt.UTC)
    else:
        action.status = "reverted"
        action.reverted_at = dt.datetime.now(dt.UTC)

    await audit.log_action(
        db, action="action_reverted", actor=current, request=request,
        target_type="action", target_id=action_id,
        details={"action_type": action.action_type, "target": action.target},
    )
    await db.commit()
    await db.refresh(action)
    return action


@router.delete("/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action(
    action_id: uuid.UUID, db: DbSession, current: CurrentUser,
) -> None:
    action = await _action_in_org_or_404(db, action_id, current.org_id)
    await db.delete(action)
    await db.commit()
