"""REST GET /api/v1/hosts/:id/events — consulta eventos do Loki para a UI."""

from __future__ import annotations

import datetime as dt
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.models import Host
from app.schemas.event import EventResponse
from app.services import loki, pii

router = APIRouter(prefix="/api/v1/hosts", tags=["events"])


@router.get("/{host_id}/events", response_model=list[EventResponse])
async def list_events(
    host_id: uuid.UUID,
    db: DbSession,
    current: CurrentUser,
    source: str | None = Query(
        default=None,
        # Allow-list — anti LogQL injection via interpolacao em loki.py.
        # Mesma lista do frontend SOURCES (EventsTab).
        pattern=r"^(sshd|selinux|apparmor|yara|clamav|fail2ban|rkhunter|chkrootkit|lynis|aide|quarantine)$",
    ),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=500),
    mask_pii: bool = Query(default=False, description="LGPD: mascara IPs/emails/CPF na resposta"),
) -> list[EventResponse]:
    host = await db.get(Host, host_id)
    if host is None or host.org_id != current.org_id:
        raise HTTPException(status_code=404, detail="host nao encontrado")

    since = dt.datetime.now(dt.UTC) - dt.timedelta(hours=hours)
    try:
        events = await loki.query_for_host(str(host_id), source=source, since=since, limit=limit)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Loki indisponivel: {e}") from e

    out: list[EventResponse] = []
    for e in events:
        raw = pii.mask_string(e.raw) if mask_pii else e.raw
        fields = pii.mask_dict(e.fields) if mask_pii else e.fields
        out.append(EventResponse(
            event_id=e.event_id,
            timestamp=e.timestamp,
            source=e.source,
            severity=e.severity,
            raw=raw,
            fields=fields,
        ))
    return out
