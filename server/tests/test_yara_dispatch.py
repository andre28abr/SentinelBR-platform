"""Testes do mapeamento Action -> pb.Command e da task de scheduled scan YARA."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.grpc_server.agent_servicer import _action_to_command
from app.models import Action, Host
from app.workers import yara_schedule


def test_action_to_command_run_yara_scan() -> None:
    a = Action(
        id=uuid.uuid4(),
        host_id=uuid.uuid4(),
        action_type="run_yara_scan",
        target="/var/www",
        reason="manual_ui",
        status="pending",
    )
    cmd = _action_to_command(a)
    assert cmd.id == str(a.id)
    assert cmd.WhichOneof("payload") == "run_yara_scan"
    assert cmd.run_yara_scan.path == "/var/www"
    assert cmd.run_yara_scan.reason == "manual_ui"


def test_action_to_command_quarantine_file() -> None:
    a = Action(
        id=uuid.uuid4(),
        host_id=uuid.uuid4(),
        action_type="quarantine_file",
        target="/var/www/evil.php",
        reason="alert:yara_critical_match:WebshellPHP",
        status="pending",
    )
    cmd = _action_to_command(a)
    assert cmd.WhichOneof("payload") == "quarantine_file"
    assert cmd.quarantine_file.file_path == "/var/www/evil.php"
    assert "WebshellPHP" in cmd.quarantine_file.reason


def test_action_to_command_unknown_type_returns_empty_payload() -> None:
    a = Action(
        id=uuid.uuid4(),
        host_id=uuid.uuid4(),
        action_type="something_unknown",
        target="x",
        reason="y",
        status="pending",
    )
    cmd = _action_to_command(a)
    assert cmd.id == str(a.id)
    assert cmd.WhichOneof("payload") is None


@pytest.mark.asyncio
async def test_schedule_creates_actions_for_each_active_host(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
) -> None:
    h1 = Host(name="a", hostname="a.local", status="active")
    h2 = Host(name="b", hostname="b.local", status="active")
    inactive = Host(name="c", hostname="c.local", status="inactive")
    db_session.add_all([h1, h2, inactive])
    await db_session.commit()

    # Patcha SessionLocal pra usar o engine de teste
    from app.db import async_sessionmaker
    test_session_factory = async_sessionmaker(
        db_session.bind, expire_on_commit=False, class_=type(db_session),
    )
    monkeypatch.setattr(yara_schedule, "SessionLocal", test_session_factory)

    # paths configurados via settings
    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("SENTINELBR_YARA_SCHEDULED_PATHS", "/var/www,/tmp")

    result = await yara_schedule._schedule_async()
    assert result["hosts"] == 2
    assert result["actions_created"] == 4  # 2 hosts x 2 paths

    actions = (await db_session.execute(select(Action))).scalars().all()
    assert len(actions) == 4
    assert all(a.action_type == "run_yara_scan" for a in actions)
    assert all(a.reason == "scheduled" for a in actions)


@pytest.mark.asyncio
async def test_schedule_skips_existing_pending(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
) -> None:
    h = Host(name="a", hostname="a.local", status="active")
    db_session.add(h)
    await db_session.commit()
    await db_session.refresh(h)

    # ja existe um scan pending pra /var/www
    db_session.add(Action(
        host_id=h.id, action_type="run_yara_scan", target="/var/www",
        reason="prev", status="pending",
    ))
    await db_session.commit()

    from app.db import async_sessionmaker
    test_session_factory = async_sessionmaker(
        db_session.bind, expire_on_commit=False, class_=type(db_session),
    )
    monkeypatch.setattr(yara_schedule, "SessionLocal", test_session_factory)

    from app.config import get_settings
    get_settings.cache_clear()
    monkeypatch.setenv("SENTINELBR_YARA_SCHEDULED_PATHS", "/var/www,/tmp")

    result = await yara_schedule._schedule_async()
    assert result["actions_created"] == 1  # so /tmp; /var/www ja existia
    assert result["skipped"] == 1
