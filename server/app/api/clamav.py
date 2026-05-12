"""REST endpoints ClamAV — dispara scan manual via Action."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import DbSession, OperatorUser
from app.models import Action
from app.schemas.action import ActionResponse
from app.services.actions import create_pending_action, get_host_in_org_or_404

router = APIRouter(prefix="/api/v1/hosts", tags=["clamav"])

# Allow-list de prefixes — anti path traversal e anti scan de paths sensiveis
# (ex: /etc/shadow, /root/.ssh). Operator nao consegue ler conteudo via
# matches do clamav fora desses paths.
ALLOWED_SCAN_PREFIXES = ("/var/www", "/var/log", "/tmp", "/home", "/opt", "/srv")  # noqa: S108


class ClamavScanRequest(BaseModel):
    path: str = Field(min_length=1, max_length=512, description="diretorio ou arquivo a escanear")
    reason: str = Field(default="manual_ui", max_length=100)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        # Anti traversal: rejeita .., trailing /.., etc.
        if ".." in v or not v.startswith("/"):
            raise ValueError("path deve ser absoluto e nao conter '..'")
        if not any(v.startswith(prefix) for prefix in ALLOWED_SCAN_PREFIXES):
            raise ValueError(
                f"path fora do allow-list. Permitidos: {', '.join(ALLOWED_SCAN_PREFIXES)}",
            )
        return v


@router.post(
    "/{host_id}/clamav-scan",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_clamav_scan(
    host_id: uuid.UUID,
    payload: ClamavScanRequest,
    request: Request,
    db: DbSession,
    current: OperatorUser,
) -> Action:
    """Cria Action 'run_clamav_scan' enviada ao agente no proximo heartbeat."""
    host = await get_host_in_org_or_404(db, host_id, current.org_id)
    if not host.clamav_installed:
        raise HTTPException(
            status_code=400,
            detail="ClamAV nao esta instalado no host (sudo apt install clamav)",
        )
    return await create_pending_action(
        db,
        host=host,
        actor=current,
        request=request,
        action_type="run_clamav_scan",
        target=payload.path,
        reason=payload.reason,
        audit_action="clamav_scan_triggered",
        audit_details={"path": payload.path, "reason": payload.reason},
        conflict_detail="ja existe scan pendente desse path nesse host",
    )
