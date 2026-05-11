"""Testes do loader + evaluator de regras (sem dependencia de DB ou Loki)."""

from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path

import pytest

from app.services.loki import QueriedEvent
from app.services.rules.evaluator import evaluate
from app.services.rules.loader import (
    Aggregate,
    Rule,
    load_default_rules,
    parse_rule,
)


def _ev(
    *,
    source: str = "sshd",
    severity: str = "warn",
    fields: dict[str, str] | None = None,
    seconds_ago: int = 0,
) -> QueriedEvent:
    return QueriedEvent(
        event_id=str(uuid.uuid4()),
        host_id="host-1",
        timestamp=dt.datetime.now(dt.UTC) - dt.timedelta(seconds=seconds_ago),
        source=source,
        severity=severity,
        raw="raw line",
        fields=fields or {},
    )


def test_default_rules_load_all_files() -> None:
    rules = load_default_rules()
    ids = {r.id for r in rules}
    assert ids == {
        "ssh_brute_force_ip",
        "ssh_brute_force_user",
        "ssh_user_enumeration",
        "ssh_root_login_failure",
        "selinux_denials_burst",
        "apparmor_denials_burst",
        "yara_critical_match",
        "yara_match_burst",
    }


def test_parse_rule_rejects_invalid_severity() -> None:
    with pytest.raises(ValueError, match="severity"):
        parse_rule({
            "id": "x",
            "name": "x",
            "severity": "BANANA",
            "source": "sshd",
        })


def test_evaluate_brute_force_ip_triggers_at_threshold() -> None:
    rule = Rule(
        id="ssh_brute_force_ip",
        name="SSH brute-force IP",
        description="",
        severity="high",
        source="sshd",
        filter_fields={"event.action": "ssh_login", "event.outcome": "failure"},
        window_seconds=60,
        aggregate=Aggregate(group_by=("source.ip",), threshold=5),
    )

    fields = {
        "event.action": "ssh_login",
        "event.outcome": "failure",
        "source.ip": "203.0.113.42",
    }
    events = [_ev(fields=fields) for _ in range(5)]

    cands = evaluate(rule, events)
    assert len(cands) == 1
    assert cands[0].count == 5
    assert cands[0].group_key == {"source.ip": "203.0.113.42"}
    assert cands[0].dedup_key() == "source.ip=203.0.113.42"


def test_evaluate_below_threshold_returns_empty() -> None:
    rule = Rule(
        id="t",
        name="t",
        description="",
        severity="high",
        source="sshd",
        filter_fields={"event.outcome": "failure"},
        aggregate=Aggregate(group_by=("source.ip",), threshold=5),
    )
    events = [_ev(fields={"event.outcome": "failure", "source.ip": "1.2.3.4"}) for _ in range(4)]
    assert evaluate(rule, events) == []


def test_evaluate_groups_separately_by_ip() -> None:
    rule = Rule(
        id="t",
        name="t",
        description="",
        severity="high",
        source="sshd",
        filter_fields={"event.outcome": "failure"},
        aggregate=Aggregate(group_by=("source.ip",), threshold=3),
    )
    events = (
        [_ev(fields={"event.outcome": "failure", "source.ip": "1.1.1.1"}) for _ in range(3)]
        + [_ev(fields={"event.outcome": "failure", "source.ip": "2.2.2.2"}) for _ in range(4)]
        + [_ev(fields={"event.outcome": "failure", "source.ip": "3.3.3.3"}) for _ in range(2)]
    )

    cands = evaluate(rule, events)
    ips = sorted(c.group_key["source.ip"] for c in cands)
    assert ips == ["1.1.1.1", "2.2.2.2"]
    counts = {c.group_key["source.ip"]: c.count for c in cands}
    assert counts == {"1.1.1.1": 3, "2.2.2.2": 4}


def test_evaluate_filter_excludes_other_outcomes() -> None:
    rule = Rule(
        id="t",
        name="t",
        description="",
        severity="high",
        source="sshd",
        filter_fields={"event.action": "ssh_login", "event.outcome": "failure"},
        aggregate=Aggregate(group_by=("source.ip",), threshold=2),
    )
    events = [
        _ev(fields={"event.action": "ssh_login", "event.outcome": "success", "source.ip": "1.1.1.1"}),
        _ev(fields={"event.action": "ssh_login", "event.outcome": "failure", "source.ip": "1.1.1.1"}),
        _ev(fields={"event.action": "ssh_login", "event.outcome": "failure", "source.ip": "1.1.1.1"}),
    ]
    cands = evaluate(rule, events)
    assert len(cands) == 1
    assert cands[0].count == 2  # so as 2 falhas


def test_evaluate_filter_excludes_other_sources() -> None:
    rule = Rule(
        id="t", name="t", description="", severity="high", source="sshd",
        filter_fields={}, aggregate=Aggregate(group_by=("source.ip",), threshold=1),
    )
    events = [
        _ev(source="sudo", fields={"source.ip": "1.1.1.1"}),
        _ev(source="sshd", fields={"source.ip": "1.1.1.1"}),
    ]
    cands = evaluate(rule, events)
    assert len(cands) == 1


def test_real_rules_match_brute_force_fixture() -> None:
    """Carrega regras reais de YAML e testa contra fixture sintetica do brute force."""
    rules = {r.id: r for r in load_default_rules()}
    rule = rules["ssh_brute_force_ip"]

    # 5 falhas do mesmo IP -> deve disparar
    fields = {
        "event.action": "ssh_login",
        "event.outcome": "failure",
        "source.ip": "203.0.113.42",
        "user.name": "root",
    }
    events = [_ev(fields=fields) for _ in range(5)]
    cands = evaluate(rule, events)
    assert len(cands) == 1
    assert cands[0].count == 5
    assert "203.0.113.42" in cands[0].description()


_ = Path  # mantem import como significativo se algum teste futuro precisar
