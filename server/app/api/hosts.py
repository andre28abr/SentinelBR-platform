import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Host
from app.schemas.host import HostCreate, HostResponse, HostUpdate

router = APIRouter(prefix="/api/v1/hosts", tags=["hosts"])


@router.get("", response_model=list[HostResponse])
async def list_hosts(db: DbSession, _: CurrentUser) -> list[Host]:
    result = await db.execute(select(Host).order_by(Host.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=HostResponse, status_code=status.HTTP_201_CREATED)
async def create_host(payload: HostCreate, db: DbSession, current: CurrentUser) -> Host:
    host = Host(
        name=payload.name,
        hostname=payload.hostname,
        created_by_id=current.id,
    )
    db.add(host)
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
async def delete_host(host_id: uuid.UUID, db: DbSession, _: CurrentUser) -> None:
    host = await db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host nao encontrado")
    await db.delete(host)
    await db.commit()
