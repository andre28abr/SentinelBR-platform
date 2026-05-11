"""Implementacao do AgentService gRPC.

Autenticacao: mTLS (CA propria assina certs no enrollment).
host_id eh extraido do CN do cert do cliente, validado contra a tabela hosts.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

from app.db import SessionLocal
from app.grpc_server.pb import agent_pb2, agent_pb2_grpc
from app.models import Host
from app.services import loki

log = logging.getLogger(__name__)


def _peer_host_id(context: grpc.aio.ServicerContext) -> uuid.UUID | None:
    """Extrai o CN (host_id) do cert que o cliente apresentou no handshake mTLS.

    Retorna None se nao houver cert (mTLS desligado em testes).
    """
    auth_ctx = context.auth_context()
    cn_list = auth_ctx.get("x509_common_name", [])
    if not cn_list:
        return None
    try:
        return uuid.UUID(cn_list[0].decode())
    except (ValueError, AttributeError):
        return None


class AgentServicer(agent_pb2_grpc.AgentServiceServicer):
    async def Heartbeat(  # noqa: N802 (nome vem do proto)
        self,
        request: agent_pb2.HeartbeatRequest,
        context: grpc.aio.ServicerContext,
    ) -> agent_pb2.HeartbeatResponse:
        peer_id = _peer_host_id(context)
        request_id = uuid.UUID(request.host_id)

        if peer_id is not None and peer_id != request_id:
            await context.abort(
                grpc.StatusCode.PERMISSION_DENIED,
                f"cert CN ({peer_id}) nao bate com host_id do request ({request_id})",
            )

        async with SessionLocal() as db:
            host = await db.get(Host, request_id)
            if host is None:
                await context.abort(grpc.StatusCode.NOT_FOUND, "host nao registrado")
            host.last_heartbeat = dt.datetime.now(dt.UTC)
            host.status = "active"
            await db.commit()
            log.info("heartbeat", extra={"host_id": str(request_id)})

        ts = Timestamp()
        ts.GetCurrentTime()
        return agent_pb2.HeartbeatResponse(server_ts=ts)

    async def Enroll(  # noqa: N802
        self,
        request: agent_pb2.EnrollRequest,
        context: grpc.aio.ServicerContext,
    ) -> agent_pb2.EnrollResponse:
        # Enrollment usa REST (precisa ser sem mTLS — o agente ainda nao tem cert).
        # Esse handler existe so pra completar o contrato; retorna UNIMPLEMENTED.
        await context.abort(
            grpc.StatusCode.UNIMPLEMENTED,
            "use POST /api/v1/agents/enroll — gRPC enroll requer mTLS pre-existente",
        )

    async def StreamEvents(  # noqa: N802
        self,
        request_iterator,
        context: grpc.aio.ServicerContext,
    ):
        peer_id = _peer_host_id(context)
        if peer_id is None:
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "mTLS obrigatorio")
        log.info("StreamEvents aberto", extra={"host_id": str(peer_id)})

        batch: list[loki.IngestEvent] = []
        batch_size = 50

        async def flush() -> None:
            if not batch:
                return
            try:
                await loki.push(batch)
            except Exception as e:  # noqa: BLE001
                log.warning("falha push Loki: %s", e)
            batch.clear()

        async for event in request_iterator:
            event_host_id = uuid.UUID(event.host_id)
            if peer_id is not None and peer_id != event_host_id:
                await context.abort(
                    grpc.StatusCode.PERMISSION_DENIED,
                    "host_id no evento difere do CN do cert",
                )

            has_ts = event.ts.seconds or event.ts.nanos
            ts = event.ts.ToDatetime() if has_ts else dt.datetime.now(dt.UTC)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=dt.UTC)

            batch.append(loki.IngestEvent(
                event_id=event.event_id,
                host_id=event.host_id,
                timestamp=ts,
                source=event.source,
                severity=event.severity or "info",
                raw=event.raw,
                fields=dict(event.fields),
            ))

            yield agent_pb2.EventAck(event_id=event.event_id, stored=True)

            if len(batch) >= batch_size:
                await flush()

        await flush()
        log.info("StreamEvents fechado", extra={"host_id": str(peer_id)})
