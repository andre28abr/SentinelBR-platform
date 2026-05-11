"""Testes do RPC SubmitInventory: upsert host_packages + agendamento de scan OSV."""

from __future__ import annotations

import datetime as dt
import uuid
from unittest.mock import MagicMock, patch

import grpc
import pytest
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.grpc_server.agent_servicer import AgentServicer
from app.grpc_server.pb import agent_pb2
from app.models import Host, HostPackage


def _build_inventory(
    host_id: uuid.UUID, packages: list[tuple[str, str, str]],
) -> agent_pb2.InventoryReport:
    ts = Timestamp()
    ts.GetCurrentTime()
    return agent_pb2.InventoryReport(
        host_id=str(host_id),
        source="apt",
        collected_at=ts,
        packages=[
            agent_pb2.PackageInfo(name=n, version=v, arch=a) for n, v, a in packages
        ],
    )


def _mock_context(peer_cn: uuid.UUID | None = None) -> MagicMock:
    """Contexto gRPC fake — simula o comportamento de auth_context()."""
    ctx = MagicMock()
    if peer_cn is None:
        ctx.auth_context.return_value = {}
    else:
        ctx.auth_context.return_value = {"x509_common_name": [str(peer_cn).encode()]}

    async def abort(code, msg):
        raise grpc.RpcError(f"{code}: {msg}")

    ctx.abort.side_effect = abort
    return ctx


@pytest.mark.asyncio
async def test_submit_inventory_upserts_packages(db_session: AsyncSession) -> None:
    host = Host(name="test-host", hostname="test.local", status="active")
    db_session.add(host)
    await db_session.commit()
    await db_session.refresh(host)

    # SessionLocal global precisa apontar pro mesmo engine de teste
    from app.db import async_sessionmaker
    test_sf = async_sessionmaker(
        db_session.bind, expire_on_commit=False, class_=type(db_session),
    )

    request = _build_inventory(host.id, [
        ("openssl", "1.1.1n-0+deb11u5", "arm64"),
        ("sudo", "1.9.5p2-3", "arm64"),
        ("bash", "5.1-2+deb11u1", "arm64"),
    ])
    ctx = _mock_context(peer_cn=host.id)

    with patch("app.grpc_server.agent_servicer.SessionLocal", test_sf), \
         patch("app.grpc_server.agent_servicer.vuln_tasks.scan_host") as mock_scan:
        mock_scan.delay.return_value = None
        servicer = AgentServicer()
        ack = await servicer.SubmitInventory(request, ctx)

    assert ack.packages_received == 3
    assert ack.scan_scheduled is True
    mock_scan.delay.assert_called_once_with(str(host.id))

    # Verifica persistencia
    pkgs = (await db_session.execute(
        select(HostPackage).where(HostPackage.host_id == host.id)
    )).scalars().all()
    assert len(pkgs) == 3
    assert {p.name for p in pkgs} == {"openssl", "sudo", "bash"}
    assert all(p.source == "apt" for p in pkgs)


@pytest.mark.asyncio
async def test_submit_inventory_replaces_old_snapshot(db_session: AsyncSession) -> None:
    """Re-submit substitui snapshot anterior — pacotes removidos somem."""
    host = Host(name="test-host", hostname="test.local", status="active")
    db_session.add(host)
    await db_session.commit()
    await db_session.refresh(host)

    # snapshot inicial: 2 pacotes velhos
    db_session.add(HostPackage(
        host_id=host.id, name="curl", version="7.68", arch="arm64", source="apt",
        last_seen_at=dt.datetime.now(dt.UTC),
    ))
    db_session.add(HostPackage(
        host_id=host.id, name="vim", version="8.2", arch="arm64", source="apt",
        last_seen_at=dt.datetime.now(dt.UTC),
    ))
    await db_session.commit()

    from app.db import async_sessionmaker
    test_sf = async_sessionmaker(
        db_session.bind, expire_on_commit=False, class_=type(db_session),
    )

    # Re-submit com apenas 1 pacote (vim foi removido, curl mantido)
    request = _build_inventory(host.id, [("curl", "7.74", "arm64")])
    ctx = _mock_context(peer_cn=host.id)

    with patch("app.grpc_server.agent_servicer.SessionLocal", test_sf), \
         patch("app.grpc_server.agent_servicer.vuln_tasks.scan_host"):
        servicer = AgentServicer()
        await servicer.SubmitInventory(request, ctx)

    pkgs = (await db_session.execute(
        select(HostPackage).where(HostPackage.host_id == host.id)
    )).scalars().all()
    assert len(pkgs) == 1
    assert pkgs[0].name == "curl"
    assert pkgs[0].version == "7.74"


@pytest.mark.asyncio
async def test_submit_inventory_rejects_cn_mismatch(db_session: AsyncSession) -> None:
    host = Host(name="test-host", hostname="test.local", status="active")
    other = Host(name="other", hostname="other.local", status="active")
    db_session.add_all([host, other])
    await db_session.commit()
    await db_session.refresh(host)
    await db_session.refresh(other)

    from app.db import async_sessionmaker
    test_sf = async_sessionmaker(
        db_session.bind, expire_on_commit=False, class_=type(db_session),
    )

    # Cliente apresenta cert de "other", mas request diz que é o "host"
    request = _build_inventory(host.id, [("openssl", "1.1", "arm64")])
    ctx = _mock_context(peer_cn=other.id)

    with patch("app.grpc_server.agent_servicer.SessionLocal", test_sf), \
         pytest.raises(grpc.RpcError, match="PERMISSION_DENIED"):
        servicer = AgentServicer()
        await servicer.SubmitInventory(request, ctx)


@pytest.mark.asyncio
async def test_submit_inventory_404_unknown_host(db_session: AsyncSession) -> None:
    from app.db import async_sessionmaker
    test_sf = async_sessionmaker(
        db_session.bind, expire_on_commit=False, class_=type(db_session),
    )

    fake_id = uuid.uuid4()
    request = _build_inventory(fake_id, [("openssl", "1.1", "arm64")])
    ctx = _mock_context(peer_cn=fake_id)

    with patch("app.grpc_server.agent_servicer.SessionLocal", test_sf), \
         pytest.raises(grpc.RpcError, match="NOT_FOUND"):
        servicer = AgentServicer()
        await servicer.SubmitInventory(request, ctx)
