"""REST endpoints da Knowledge Base — MITRE ATT&CK PT-BR + hunting + playbooks.

Tudo read-only e publico para usuario autenticado (nao tem dado sensivel).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

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
