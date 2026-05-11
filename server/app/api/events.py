"""REST GET /api/v1/hosts/:id/events — consulta eventos do Loki para a UI."""

from __future__ import annotations

import datetime as dt
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import CurrentUser, DbSession
from app.models import Host
from app.schemas.event import EventResponse
from app.services import loki

router = APIRouter(prefix="/api/v1/hosts", tags=["events"])


@router.get("/{host_id}/events", response_model=list[EventResponse])
async def list_events(
    host_id: uuid.UUID,
    db: DbSession,
    _: CurrentUser,
    source: str | None = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[EventResponse]:
    host = await db.get(Host, host_id)
    if host is None:
        raise HTTPException(status_code=404, detail="host nao encontrado")

    since = dt.datetime.now(dt.UTC) - dt.timedelta(hours=hours)
    try:
        events = await loki.query_for_host(str(host_id), source=source, since=since, limit=limit)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Loki indisponivel: {e}") from e

    return [
        EventResponse(
            event_id=e.event_id,
            timestamp=e.timestamp,
            source=e.source,
            severity=e.severity,
            raw=e.raw,
            fields=e.fields,
        )
        for e in events
    ]
