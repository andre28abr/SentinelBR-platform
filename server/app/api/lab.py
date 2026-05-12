"""REST endpoints do Lab Mode — controle de VMs OrbStack pra demo.

GUARDAS DE SEGURANCA:
- Todos endpoints (exceto /lab/status) chamam `require_lab_mode` que 404
  se settings.lab_mode=false. Em prod sem lab_mode, a API se comporta
  como se /lab/* nao existisse.
- Endpoints exigem AdminUser — operator/viewer nao operam VMs.
- Reset apaga alerts/actions/events da org do user atual; nunca cross-org.
- Reset NUNCA apaga hosts (precisaria re-enroll pra trazer de volta) nem
  audit_logs (LGPD: retencao obrigatoria).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete

from app.api.deps import AdminUser, DbSession
from app.config import get_settings
from app.models import Action, Alert, Host
from app.services import audit, lab

router = APIRouter(prefix="/api/v1/lab", tags=["lab"])


def require_lab_mode() -> None:
    """Dependency: 404 se SENTINELBR_LAB_MODE!=true. Esconde a API em prod."""
    if not get_settings().lab_mode:
        raise HTTPException(
            status_code=404,
            detail="lab mode desabilitado (set SENTINELBR_LAB_MODE=true em dev)",
        )


# Schemas


class LabStatusResponse(BaseModel):
    enabled: bool
    """True se lab_mode esta ativo. UI usa pra mostrar banner + aba /lab."""


class VmInfoResponse(BaseModel):
    name: str
    state: str
    distro: str
    arch: str


class VmActionResponse(BaseModel):
    name: str
    action: str  # "start" | "stop" | "attack"
    ok: bool
    detail: str = ""


class ResetResponse(BaseModel):
    alerts_deleted: int
    actions_deleted: int
    detail: str = "ok"


# Endpoints


@router.get("/status", response_model=LabStatusResponse)
async def status_endpoint() -> LabStatusResponse:
    """Single-source-of-truth pro frontend: lab_mode ligado?

    PUBLICO (sem auth) de proposito: a LoginPage precisa do flag pra
    mostrar o banner "demo environment" antes do user logar. Vazar o
    boolean nao eh sensivel — qualquer um que toque /lab/* ja descobriria.
    """
    return LabStatusResponse(enabled=get_settings().lab_mode)


@router.get("/vms", response_model=list[VmInfoResponse],
            dependencies=[Depends(require_lab_mode)])
async def list_vms_endpoint(_: AdminUser) -> list[VmInfoResponse]:
    try:
        vms = await lab.list_vms()
    except lab.LabError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return [VmInfoResponse(name=v.name, state=v.state, distro=v.distro, arch=v.arch)
            for v in vms]


@router.post("/vms/{name}/start", response_model=VmActionResponse,
             status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(require_lab_mode)])
async def start_vm_endpoint(
    name: str, request: Request, db: DbSession, current: AdminUser,
) -> VmActionResponse:
    try:
        await lab.start_vm(name)
    except lab.InvalidVmNameError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except lab.LabError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    await audit.log_action(
        db, action="lab_vm_started", actor=current, request=request,
        target_type="lab_vm", target_id=None, details={"vm": name},
    )
    await db.commit()
    return VmActionResponse(name=name, action="start", ok=True)


@router.post("/vms/{name}/stop", response_model=VmActionResponse,
             status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(require_lab_mode)])
async def stop_vm_endpoint(
    name: str, request: Request, db: DbSession, current: AdminUser,
) -> VmActionResponse:
    try:
        await lab.stop_vm(name)
    except lab.InvalidVmNameError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except lab.LabError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    await audit.log_action(
        db, action="lab_vm_stopped", actor=current, request=request,
        target_type="lab_vm", target_id=None, details={"vm": name},
    )
    await db.commit()
    return VmActionResponse(name=name, action="stop", ok=True)


@router.post("/vms/{name}/attack", response_model=VmActionResponse,
             status_code=status.HTTP_202_ACCEPTED,
             dependencies=[Depends(require_lab_mode)])
async def attack_vm_endpoint(
    name: str, request: Request, db: DbSession, current: AdminUser,
) -> VmActionResponse:
    """Re-planta iscas/brute-force numa VM especifica. Demora ~30s-1min."""
    try:
        output = await lab.attack_vm(name)
    except lab.InvalidVmNameError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except lab.LabError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    await audit.log_action(
        db, action="lab_vm_attacked", actor=current, request=request,
        target_type="lab_vm", target_id=None, details={"vm": name},
    )
    await db.commit()
    # Retorna so o trecho final do output (UI nao precisa de tudo).
    tail = "\n".join(output.strip().splitlines()[-5:])
    return VmActionResponse(name=name, action="attack", ok=True, detail=tail)


@router.post("/reset", response_model=ResetResponse,
             dependencies=[Depends(require_lab_mode)])
async def reset_demo(
    request: Request, db: DbSession, current: AdminUser,
) -> ResetResponse:
    """Apaga alerts + actions da org atual pra "limpar a tela" entre demos.

    NAO apaga: hosts (precisaria re-enroll), audit_logs (LGPD), users,
    organizations. Eventos de Loki NAO sao tocados (TTL natural cuida).
    """
    # Coleta IDs de hosts da org pra limitar o scope do delete (alerts e
    # actions tem host_id, nao org_id direto — host_id eh a porta).
    host_ids_q = (
        await db.execute(
            Host.__table__.select().with_only_columns(Host.id)
            .where(Host.org_id == current.org_id)
        )
    ).scalars().all()
    host_ids: list[uuid.UUID] = list(host_ids_q)

    if not host_ids:
        # Sem hosts, nao ha o que limpar. Retorna 0/0 sem audit (nao
        # mudou nada).
        return ResetResponse(alerts_deleted=0, actions_deleted=0,
                             detail="nenhum host na org — nada a limpar")

    alerts_res = await db.execute(
        delete(Alert).where(Alert.host_id.in_(host_ids))
    )
    actions_res = await db.execute(
        delete(Action).where(Action.host_id.in_(host_ids))
    )
    alerts_n = alerts_res.rowcount or 0
    actions_n = actions_res.rowcount or 0

    await audit.log_action(
        db, action="lab_demo_reset", actor=current, request=request,
        target_type="organization", target_id=current.org_id,
        details={"alerts_deleted": alerts_n, "actions_deleted": actions_n},
    )
    await db.commit()
    return ResetResponse(alerts_deleted=alerts_n, actions_deleted=actions_n)
