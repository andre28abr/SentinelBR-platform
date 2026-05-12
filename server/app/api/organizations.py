"""REST endpoints de Organization (tenant). Cada user pertence a 1 org.

Por enquanto MVP:
  - GET /organizations: lista a propria org (list trivial — single-org per user)
  - GET /organizations/{id}: detalhe (so se for a propria)
  - POST /organizations: cria nova (apenas admin do sistema; futuro: signup)
  - PUT /organizations/{id}: edita nome (admin da org)

Sem cross-org switching no MVP — cada login = 1 org.
"""

from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models import Organization
from app.services import audit

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)


@router.get("", response_model=list[OrganizationResponse])
async def list_organizations(
    db: DbSession, current: CurrentUser,
) -> list[Organization]:
    org = await db.get(Organization, current.org_id)
    return [org] if org is not None else []


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID, db: DbSession, current: CurrentUser,
) -> Organization:
    if org_id != current.org_id:
        raise HTTPException(status_code=404, detail="organizacao nao encontrada")
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="organizacao nao encontrada")
    return org


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
    request: Request,
    db: DbSession,
    current: AdminUser,
) -> Organization:
    if org_id != current.org_id:
        raise HTTPException(status_code=404, detail="organizacao nao encontrada")
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="organizacao nao encontrada")
    old_name = org.name
    if payload.name is not None:
        org.name = payload.name
    await audit.log_action(
        db, action="organization_updated", actor=current, request=request,
        target_type="organization", target_id=org_id,
        details={"old_name": old_name, "new_name": org.name},
    )
    await db.commit()
    await db.refresh(org)
    return org


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate, request: Request, db: DbSession, current: AdminUser,
) -> Organization:
    """Cria nova organizacao. Apenas admin (MVP — futuro: signup publico ou
    convite). NAO migra o user atual pra essa nova org."""
    if not re.match(r"^[a-z0-9-]+$", payload.slug):
        raise HTTPException(status_code=400, detail="slug invalido (a-z, 0-9, -)")
    org = Organization(name=payload.name, slug=payload.slug)
    db.add(org)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail="slug ja existe") from e
    await audit.log_action(
        db, action="organization_created", actor=current, request=request,
        target_type="organization", target_id=org.id,
        details={"slug": payload.slug, "name": payload.name},
    )
    await db.commit()
    await db.refresh(org)
    return org
