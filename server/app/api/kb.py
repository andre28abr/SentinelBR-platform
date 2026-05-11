"""REST endpoints da Knowledge Base — MITRE ATT&CK PT-BR + hunting + playbooks.

Tudo read-only e publico para usuario autenticado (nao tem dado sensivel).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser
from app.services import kb

router = APIRouter(prefix="/api/v1/kb", tags=["kb"])


@router.get("/techniques")
async def list_techniques(_: CurrentUser) -> list[dict]:
    return kb.list_techniques()


@router.get("/techniques/{tid}")
async def get_technique(tid: str, _: CurrentUser) -> dict:
    t = kb.get_technique(tid)
    if t is None:
        raise HTTPException(status_code=404, detail="tecnica nao encontrada")
    return t


@router.get("/hunting")
async def list_hunting_queries(_: CurrentUser) -> list[dict]:
    return kb.list_hunting_queries()


@router.get("/playbooks")
async def list_playbooks(_: CurrentUser) -> list[dict]:
    return kb.list_playbooks()


@router.get("/explain")
async def explain(
    _: CurrentUser,
    rule_id: str | None = Query(
        default=None, description="rule_id de alerta (ex: ssh_brute_force_ip)",
    ),
    action_type: str | None = Query(
        default=None, description="action_type (ex: block_ip)",
    ),
) -> dict:
    """Retorna explicacao leiga ("o que aconteceu? devo me preocupar? o que fazer?")
    pra um rule_id de alerta OU action_type. UI usa pra popover ⓘ."""
    if rule_id:
        tech = kb.explain_rule(rule_id)
        return {
            "kind": "rule",
            "key": rule_id,
            "technique": tech,  # None se nao mapeado
        }
    if action_type:
        explainer = kb.explain_action(action_type)
        return {
            "kind": "action",
            "key": action_type,
            "explainer": explainer,  # None se nao mapeado
        }
    raise HTTPException(
        status_code=400, detail="precisa de ?rule_id=... OU ?action_type=...",
    )
