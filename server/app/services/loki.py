"""Cliente HTTP do Loki: push de eventos + query de leitura.

Loki API:
    POST {loki_url}/loki/api/v1/push   — envia logs (streams + values)
    GET  {loki_url}/loki/api/v1/query_range?query=&start=&end=&limit=  — le

Estrategia de labels (cardinalidade BAIXA — Loki indexa labels):
    {host_id, source, severity}
Tudo o mais (ip, user, action, raw) vai dentro do log line como JSON, recuperavel
no UI ou via `| json | line_format` no LogQL.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import logging

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True)
class IngestEvent:
    """Forma minima do que o gRPC envia, antes de virar log line no Loki."""

    event_id: str
    host_id: str
    timestamp: dt.datetime
    source: str
    severity: str
    raw: str
    fields: dict[str, str]


@dataclasses.dataclass(slots=True)
class QueriedEvent:
    """O que sai do query_range, ja parseado pra forma usada na UI."""

    event_id: str
    host_id: str
    timestamp: dt.datetime
    source: str
    severity: str
    raw: str
    fields: dict[str, str]


def _ts_to_ns(t: dt.datetime) -> str:
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.UTC)
    return str(int(t.timestamp() * 1_000_000_000))


def _line_payload(ev: IngestEvent) -> str:
    return json.dumps({
        "event_id": ev.event_id,
        "raw": ev.raw,
        "fields": ev.fields,
    })


_LabelKey = tuple[tuple[str, str], ...]


def _group_by_labels(events: list[IngestEvent]) -> dict[_LabelKey, list[IngestEvent]]:
    groups: dict[tuple[tuple[str, str], ...], list[IngestEvent]] = {}
    for ev in events:
        labels = (
            ("host_id", ev.host_id),
            ("source", ev.source),
            ("severity", ev.severity),
        )
        groups.setdefault(labels, []).append(ev)
    return groups


async def push(events: list[IngestEvent]) -> None:
    """Envia 1+ eventos para o Loki agrupados pelas suas labels.

    Lanca httpx.HTTPError se o Loki responder erro.
    """
    if not events:
        return

    streams = []
    for labels, group in _group_by_labels(events).items():
        group_sorted = sorted(group, key=lambda e: e.timestamp)
        values = [[_ts_to_ns(ev.timestamp), _line_payload(ev)] for ev in group_sorted]
        streams.append({"stream": dict(labels), "values": values})

    settings = get_settings()
    url = f"{settings.loki_url}/loki/api/v1/push"
    async with httpx.AsyncClient(timeout=10.0) as cli:
        r = await cli.post(url, json={"streams": streams})
        r.raise_for_status()


async def query_for_host(
    host_id: str,
    *,
    source: str | None = None,
    since: dt.datetime | None = None,
    limit: int = 100,
) -> list[QueriedEvent]:
    """Consulta eventos do Loki por host (e opcionalmente source). Mais recentes primeiro."""
    selectors = [f'host_id="{host_id}"']
    if source:
        selectors.append(f'source="{source}"')
    query = "{" + ",".join(selectors) + "}"

    end = dt.datetime.now(dt.UTC)
    start = since or (end - dt.timedelta(hours=24))

    settings = get_settings()
    url = f"{settings.loki_url}/loki/api/v1/query_range"
    params = {
        "query": query,
        "start": _ts_to_ns(start),
        "end": _ts_to_ns(end),
        "limit": str(limit),
        "direction": "backward",  # mais recentes primeiro
    }

    async with httpx.AsyncClient(timeout=10.0) as cli:
        r = await cli.get(url, params=params)
        r.raise_for_status()
        body = r.json()

    out: list[QueriedEvent] = []
    for stream in body.get("data", {}).get("result", []):
        labels = stream.get("stream", {})
        for ts_ns, line in stream.get("values", []):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                payload = {"raw": line, "event_id": "", "fields": {}}
            out.append(QueriedEvent(
                event_id=payload.get("event_id", ""),
                host_id=labels.get("host_id", host_id),
                timestamp=dt.datetime.fromtimestamp(int(ts_ns) / 1e9, tz=dt.UTC),
                source=labels.get("source", ""),
                severity=labels.get("severity", "info"),
                raw=payload.get("raw", line),
                fields=payload.get("fields", {}),
            ))
    out.sort(key=lambda e: e.timestamp, reverse=True)
    return out[:limit]
