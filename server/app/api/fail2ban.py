"""REST endpoints fail2ban — unban/ban IP via Action enviada ao agente."""

from __future__ import annotations

import ipaddress
import re
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import DbSession, OperatorUser
from app.models import Action
from app.schemas.action import ActionResponse
from app.services.actions import create_pending_action, get_host_in_org_or_404

router = APIRouter(prefix="/api/v1/hosts", tags=["fail2ban"])

# fail2ban jail names sao alfanumericos + dash/underscore (sshd, apache-auth, ...)
_JAIL_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


class Fail2banActionRequest(BaseModel):
    jail: str = Field(min_length=1, max_length=64)
    ip: str = Field(min_length=1, max_length=45)  # IPv4 ou IPv6
    reason: str = Field(default="manual_ui", max_length=255)

    @field_validator("jail")
    @classmethod
    def validate_jail(cls, v: str) -> str:
        if not _JAIL_PATTERN.match(v):
            raise ValueError("jail name invalido (so alfanumerico + dash/underscore)")
        return v

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        # Valida que e IP real (impede injection via target shell)
        ipaddress.ip_address(v)
        return v


async def _trigger_fail2ban(
    db, host_id: uuid.UUID, action_type: str,
    payload: Fail2banActionRequest, request: Request, current,
) -> Action:
    host = await get_host_in_org_or_404(db, host_id, current.org_id)
    if not host.fail2ban_installed:
        raise HTTPException(
            status_code=400,
            detail="fail2ban nao esta instalado no host",
        )
    target = f"{payload.jail}:{payload.ip}"
    return await create_pending_action(
        db,
        host=host,
        actor=current,
        request=request,
        action_type=action_type,
        target=target,
        reason=payload.reason,
        audit_action=f"{action_type}_triggered",
        audit_details={"jail": payload.jail, "ip": payload.ip},
        conflict_detail=f"ja existe '{action_type}' pendente pra {target}",
    )


@router.post(
    "/{host_id}/fail2ban-unban",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_fail2ban_unban(
    host_id: uuid.UUID, payload: Fail2banActionRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Desbloqueia IP num jail do fail2ban (action enviada ao agente)."""
    return await _trigger_fail2ban(
        db, host_id, "fail2ban_unban", payload, request, current,
    )


@router.post(
    "/{host_id}/fail2ban-ban",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_fail2ban_ban(
    host_id: uuid.UUID, payload: Fail2banActionRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Bloqueia IP manualmente num jail (action enviada ao agente)."""
    return await _trigger_fail2ban(
        db, host_id, "fail2ban_ban", payload, request, current,
    )
