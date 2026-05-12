"""REST endpoints firewall — adicionar/remover regra via Action (Fase H6).

Suporta ufw e firewalld; outros backends retornam erro 400 com sugestao de
editar manualmente no host.
"""

from __future__ import annotations

import ipaddress
import re
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import DbSession, OperatorUser
from app.models import Action, Host
from app.schemas.action import ActionResponse
from app.services.actions import create_pending_action, get_host_in_org_or_404

router = APIRouter(prefix="/api/v1/hosts", tags=["firewall"])

# Port: "22" | "80,443" | "1000:2000"
_PORT_PATTERN = re.compile(r"^\d+([,:]\d+)*$")
_SUPPORTED_BACKENDS = ("ufw", "firewalld")


class FirewallAddRuleRequest(BaseModel):
    verb: Literal["allow", "deny"]
    protocol: Literal["tcp", "udp"]
    port: str = Field(min_length=1, max_length=64)
    source_cidr: str = Field(default="", max_length=64)
    reason: str = Field(default="manual_ui", max_length=255)

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: str) -> str:
        if not _PORT_PATTERN.match(v):
            raise ValueError("port deve ser '22', '80,443' ou '1000:2000'")
        return v

    @field_validator("source_cidr")
    @classmethod
    def validate_cidr(cls, v: str) -> str:
        if v == "":
            return v
        ipaddress.ip_network(v, strict=False)
        return v


class FirewallRemoveRuleRequest(BaseModel):
    rule_id: str = Field(min_length=1, max_length=512)
    reason: str = Field(default="manual_ui", max_length=255)


def _check_firewall_supported(host: Host) -> str:
    if not host.firewall_active or host.firewall_active not in _SUPPORTED_BACKENDS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"backend '{host.firewall_active or 'nenhum'}' nao suporta edicao "
                "pela UI. Edite manualmente no host (apenas ufw/firewalld suportados)."
            ),
        )
    return host.firewall_active


@router.post(
    "/{host_id}/firewall-rule",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def add_firewall_rule(
    host_id: uuid.UUID, payload: FirewallAddRuleRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Adiciona regra ao firewall ativo (ufw ou firewalld) via Action."""
    host = await get_host_in_org_or_404(db, host_id, current.org_id)
    backend = _check_firewall_supported(host)
    target = "|".join(
        [backend, payload.verb, payload.protocol, payload.port, payload.source_cidr],
    )
    return await create_pending_action(
        db,
        host=host,
        actor=current,
        request=request,
        action_type="add_firewall_rule",
        target=target,
        reason=payload.reason,
        audit_action="firewall_rule_add_triggered",
        audit_details={
            "backend": backend, "verb": payload.verb, "protocol": payload.protocol,
            "port": payload.port, "source_cidr": payload.source_cidr,
        },
        conflict_detail="regra ja pendente",
    )


@router.delete(
    "/{host_id}/firewall-rule",
    response_model=ActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def remove_firewall_rule(
    host_id: uuid.UUID, payload: FirewallRemoveRuleRequest, request: Request,
    db: DbSession, current: OperatorUser,
) -> Action:
    """Remove regra do firewall ativo via Action."""
    host = await get_host_in_org_or_404(db, host_id, current.org_id)
    backend = _check_firewall_supported(host)
    target = f"{backend}|{payload.rule_id}"
    return await create_pending_action(
        db,
        host=host,
        actor=current,
        request=request,
        action_type="remove_firewall_rule",
        target=target,
        reason=payload.reason,
        audit_action="firewall_rule_remove_triggered",
        audit_details={"backend": backend, "rule_id": payload.rule_id},
        conflict_detail="remocao ja pendente",
    )
