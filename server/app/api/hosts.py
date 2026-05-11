import uuid

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.models import Host
from app.schemas.enrollment import EnrollmentTokenResponse
from app.schemas.host import HostCreate, HostResponse, HostUpdate
from app.services import audit, enrollment

router = APIRouter(prefix="/api/v1/hosts", tags=["hosts"])


@router.get("", response_model=list[HostResponse])
async def list_hosts(db: DbSession, _: CurrentUser) -> list[Host]:
    result = await db.execute(select(Host).order_by(Host.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(
    payload: HostCreate, request: Request, db: DbSession, current: CurrentUser
) -> Host:
    host = Host(
        name=payload.name,
        hostname=payload.hostname,
        created_by_id=current.id,
    )
    db.add(host)
    await db.flush()
    await audit.log_action(
        db, action="host_created", actor=current, request=request,
        target_type="host", target_id=host.id,
        details={"name": host.name, "hostname": host.hostname},
    )
    await db.commit()
    await db.refresh(host)
    return host


@router.get("/{host_id}", response_model=HostResponse)
async def get_host(host_id: uuid.UUID, db: DbSession, _: CurrentUser) -> Host:
    host = await db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    return host


@router.put("/{host_id}", response_model=HostResponse)
async def update_host(
    host_id: uuid.UUID, payload: HostUpdate, db: DbSession, _: CurrentUser
) -> Host:
    host = await db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    if payload.name is not None:
        host.name = payload.name
    if payload.hostname is not None:
        host.hostname = payload.hostname
    await db.commit()
    await db.refresh(host)
    return host


@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_host(
    host_id: uuid.UUID, request: Request, db: DbSession, current: CurrentUser
) -> None:
    host = await db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    await audit.log_action(
        db, action="host_deleted", actor=current, request=request,
        target_type="host", target_id=host_id,
        details={"name": host.name, "hostname": host.hostname},
    )
    await db.delete(host)
    await db.commit()


@router.post(
    "/{host_id}/enrollment-token",
    response_model=EnrollmentTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def mint_enrollment_token(
    host_id: uuid.UUID, db: DbSession, _: CurrentUser
) -> EnrollmentTokenResponse:
    host = await db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host nao encontrado")

    token, expires_at = await enrollment.mint_token(db, host)
    settings = get_settings()
    return EnrollmentTokenResponse(
        token=token,
        expires_at=expires_at,
        install_command=enrollment.install_command(
            host_id=host.id,
            token=token,
            server_endpoint=settings.public_endpoint,
            grpc_endpoint=settings.grpc_public_endpoint,
        ),
    )
