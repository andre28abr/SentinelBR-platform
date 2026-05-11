"""Implementacao do AgentService gRPC.

Autenticacao: mTLS (CA propria assina certs no enrollment).
host_id eh extraido do CN do cert do cliente, validado contra a tabela hosts.
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import logging
import uuid

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy import select

from app.db import SessionLocal
from app.grpc_server.pb import agent_pb2, agent_pb2_grpc
from app.models import Action, Host, HostPackage
from app.services import loki
from app.workers import vuln as vuln_tasks

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


def _action_to_command(action: Action) -> agent_pb2.Command:
    cmd = agent_pb2.Command(id=str(action.id))
    if action.action_type == "block_ip":
        cmd.block_ip.CopyFrom(agent_pb2.BlockIPCommand(
            ip=action.target,
            duration_seconds=0,
            reason=action.reason,
        ))
    elif action.action_type == "unblock_ip":
        cmd.unblock_ip.CopyFrom(agent_pb2.UnblockIPCommand(ip=action.target))
    elif action.action_type == "run_yara_scan":
        cmd.run_yara_scan.CopyFrom(agent_pb2.RunYaraScanCommand(
            path=action.target,
            reason=action.reason,
        ))
    elif action.action_type == "quarantine_file":
        cmd.quarantine_file.CopyFrom(agent_pb2.QuarantineFileCommand(
            file_path=action.target,
            reason=action.reason,
        ))
    elif action.action_type == "run_clamav_scan":
        cmd.run_clamav_scan.CopyFrom(agent_pb2.RunClamavScanCommand(
            path=action.target,
            reason=action.reason,
        ))
    return cmd


async def _apply_command_results(
    db, host_id: uuid.UUID, results: list[agent_pb2.CommandResult]
) -> None:
    """Marca actions como executed/failed conforme o agente reportou."""
    if not results:
        return
    for result in results:
        try:
            action_id = uuid.UUID(result.command_id)
        except ValueError:
            continue
        action = await db.get(Action, action_id)
        if action is None or action.host_id != host_id:
            continue
        if result.status == agent_pb2.COMMAND_STATUS_OK:
            action.status = "executed"
        elif result.status == agent_pb2.COMMAND_STATUS_FAILED:
            action.status = "failed"
            action.error_message = result.error_message
        elif result.status == agent_pb2.COMMAND_STATUS_UNSUPPORTED:
            action.status = "failed"
            action.error_message = f"unsupported: {result.error_message}"
        if result.executed_at.seconds or result.executed_at.nanos:
            action.executed_at = result.executed_at.ToDatetime().replace(tzinfo=dt.UTC)
        else:
            action.executed_at = dt.datetime.now(dt.UTC)


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

        pending_pb_commands: list[agent_pb2.Command] = []
        async with SessionLocal() as db:
            host = await db.get(Host, request_id)
            if host is None:
                await context.abort(grpc.StatusCode.NOT_FOUND, "host nao registrado")
            host.last_heartbeat = dt.datetime.now(dt.UTC)
            host.status = "active"

            # Snapshot dos stats reportados (se vieram)
            if request.HasField("stats"):
                stats = request.stats
                if stats.ip_address:
                    host.ip_address = stats.ip_address
                if stats.cpu_count:
                    host.cpu_count = stats.cpu_count
                if stats.load_avg_1m:
                    host.load_avg_1m = stats.load_avg_1m
                if stats.mem_total_bytes:
                    host.mem_used_bytes = stats.mem_used_bytes
                    host.mem_total_bytes = stats.mem_total_bytes
                if stats.disk_total_bytes:
                    host.disk_used_bytes = stats.disk_used_bytes
                    host.disk_total_bytes = stats.disk_total_bytes
                if stats.uptime_seconds:
                    host.uptime_seconds = stats.uptime_seconds
                # ClamAV — sempre persiste (bool pode ser False legit)
                host.clamav_installed = stats.clamav_installed
                if stats.clamav_version:
                    host.clamav_version = stats.clamav_version
                if stats.clamav_db_age_days:
                    host.clamav_db_age_days = stats.clamav_db_age_days
                # Admin counts — sempre persiste (0 eh valor valido)
                host.services_running = stats.services_running
                host.services_failed = stats.services_failed
                host.packages_upgradable = stats.packages_upgradable
                host.listening_ports = stats.listening_ports
                host.cron_jobs = stats.cron_jobs

            # 1) processa CommandResults reportados pelo agente
            await _apply_command_results(db, request_id, request.command_results)

            # 2) busca actions ainda nao executadas pra esse host e marca como 'sent'
            pending = (
                await db.execute(
                    select(Action).where(
                        Action.host_id == request_id,
                        Action.status == "pending",
                    )
                )
            ).scalars().all()
            now = dt.datetime.now(dt.UTC)
            for action in pending:
                pending_pb_commands.append(_action_to_command(action))
                action.status = "sent"
                action.sent_at = now

            await db.commit()
            log.info(
                "heartbeat",
                extra={"host_id": str(request_id), "pending_commands": len(pending_pb_commands)},
            )

        ts = Timestamp()
        ts.GetCurrentTime()
        return agent_pb2.HeartbeatResponse(server_ts=ts, pending_commands=pending_pb_commands)

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
        flush_interval_s = 2.0  # garante visibilidade rapida em dev/lab quando o batch nao enche

        async def flush() -> None:
            if not batch:
                return
            try:
                await loki.push(batch)
            except Exception as e:  # noqa: BLE001
                log.warning("falha push Loki: %s", e)
            batch.clear()

        # Flush periodico em background — fecha quando o stream fecha (cancellation).
        async def periodic_flush() -> None:
            try:
                while True:
                    await asyncio.sleep(flush_interval_s)
                    await flush()
            except asyncio.CancelledError:
                pass

        flush_task = asyncio.create_task(periodic_flush())

        try:
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
        finally:
            flush_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await flush_task
            await flush()  # last best-effort flush
            log.info("StreamEvents fechado", extra={"host_id": str(peer_id)})

    async def SubmitInventory(  # noqa: N802
        self,
        request: agent_pb2.InventoryReport,
        context: grpc.aio.ServicerContext,
    ) -> agent_pb2.InventoryAck:
        peer_id = _peer_host_id(context)
        request_id = uuid.UUID(request.host_id)
        if peer_id is not None and peer_id != request_id:
            await context.abort(
                grpc.StatusCode.PERMISSION_DENIED,
                f"cert CN ({peer_id}) nao bate com host_id do inventory ({request_id})",
            )

        async with SessionLocal() as db:
            host = await db.get(Host, request_id)
            if host is None:
                await context.abort(grpc.StatusCode.NOT_FOUND, "host nao registrado")

            # Snapshot strategy: deleta tudo do host e re-insere. Simples e correto
            # — pacotes patcheados/removidos somem do snapshot atual.
            from sqlalchemy import delete
            await db.execute(delete(HostPackage).where(HostPackage.host_id == request_id))

            seen: set[tuple[str, str]] = set()
            for pkg in request.packages:
                key = (pkg.name, pkg.arch or "")
                if key in seen:
                    continue
                seen.add(key)
                db.add(HostPackage(
                    host_id=request_id,
                    name=pkg.name,
                    version=pkg.version,
                    arch=pkg.arch or "",
                    source=request.source,
                ))
            await db.commit()
            log.info(
                "inventory recebido", extra={
                    "host_id": str(request_id), "packages": len(seen), "source": request.source,
                },
            )

        # Agenda scan OSV em background (fire-and-forget — vuln_scan eh idempotente).
        try:
            vuln_tasks.scan_host.delay(str(request_id))
            scan_scheduled = True
        except Exception as e:  # noqa: BLE001
            log.warning("falha ao agendar scan vuln: %s", e)
            scan_scheduled = False

        return agent_pb2.InventoryAck(
            packages_received=len(request.packages),
            scan_scheduled=scan_scheduled,
        )
