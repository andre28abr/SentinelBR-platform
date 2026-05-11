"""Avalia uma regra contra uma lista de eventos e retorna AlertCandidates.

Separado da camada de DB e gRPC pra ser testavel puro:
    - input: rule + lista de QueriedEvent
    - output: AlertCandidates (host_id ainda nao plugado)

A engine (engine.py) eh quem itera por host, faz dedup contra DB, etc.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass, field

from app.services.loki import QueriedEvent
from app.services.rules.loader import Rule


@dataclass(slots=True)
class AlertCandidate:
    rule: Rule
    matched_events: list[QueriedEvent]
    group_key: dict[str, str] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.matched_events)

    @property
    def first_event_at(self) -> dt.datetime:
        return min(e.timestamp for e in self.matched_events)

    @property
    def last_event_at(self) -> dt.datetime:
        return max(e.timestamp for e in self.matched_events)

    def dedup_key(self) -> str:
        if not self.group_key:
            return "*"
        items = sorted(self.group_key.items())
        return ";".join(f"{k}={v}" for k, v in items)

    def description(self) -> str:
        if self.group_key:
            ctx = ", ".join(f"{k}={v}" for k, v in sorted(self.group_key.items()))
            return f"{self.rule.name} — {self.count} eventos ({ctx})"
        return f"{self.rule.name} — {self.count} eventos"


def _matches_filter(event: QueriedEvent, rule: Rule) -> bool:
    if event.source != rule.source:
        return False
    for key, expected in rule.filter_fields.items():
        if event.fields.get(key) != expected:
            return False
    return True


def evaluate(rule: Rule, events: Iterable[QueriedEvent]) -> list[AlertCandidate]:
    """Aplica filtro + agregacao da regra. Retorna candidatos ordenados por count desc."""
    matched = [e for e in events if _matches_filter(e, rule)]
    if not matched:
        return []

    if rule.aggregate is None:
        return [AlertCandidate(rule=rule, matched_events=matched)]

    groups: dict[tuple[str, ...], list[QueriedEvent]] = {}
    for ev in matched:
        key = tuple(ev.fields.get(f, "") for f in rule.aggregate.group_by)
        if any(v == "" for v in key):
            continue  # evento sem todos os campos do group_by — descarta
        groups.setdefault(key, []).append(ev)

    out: list[AlertCandidate] = []
    for key, group_events in groups.items():
        if len(group_events) < rule.aggregate.threshold:
            continue
        out.append(AlertCandidate(
            rule=rule,
            matched_events=group_events,
            group_key=dict(zip(rule.aggregate.group_by, key, strict=True)),
        ))
    out.sort(key=lambda c: c.count, reverse=True)
    return out
