"""Carrega regras de deteccao a partir de arquivos YAML em app/rules/.

Formato (Sigma-inspirado, simplificado):

    id: ssh_brute_force_ip          # identificador unico
    name: SSH brute-force            # nome human-readable
    description: |                   # texto livre, mostrado na UI
      ...
    severity: high                   # info | low | medium | high | critical
    source: sshd                     # casa com Event.source
    filter:                          # campos que precisam estar presentes/iguais
      event.action: ssh_login
      event.outcome: failure
    window_seconds: 60               # janela de tempo pra avaliar
    aggregate:                       # opcional — se ausente, cada match gera alerta
      group_by: [source.ip]          # campos pra agrupar
      threshold: 5                   # numero minimo de eventos no grupo
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

VALID_SEVERITIES = {"info", "low", "medium", "high", "critical"}


@dataclass(slots=True, frozen=True)
class Aggregate:
    group_by: tuple[str, ...]
    threshold: int


@dataclass(slots=True, frozen=True)
class Rule:
    id: str
    name: str
    description: str
    severity: str
    source: str
    filter_fields: dict[str, str] = field(default_factory=dict)
    window_seconds: int = 60
    aggregate: Aggregate | None = None


def parse_rule(data: dict) -> Rule:
    rid = data["id"]
    severity = data.get("severity", "medium")
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"rule {rid}: severity invalida '{severity}'")

    agg = None
    if a := data.get("aggregate"):
        group_by = a.get("group_by", [])
        if not isinstance(group_by, list) or not group_by:
            raise ValueError(f"rule {rid}: aggregate.group_by deve ser lista nao-vazia")
        agg = Aggregate(group_by=tuple(group_by), threshold=int(a.get("threshold", 1)))

    return Rule(
        id=rid,
        name=data["name"],
        description=str(data.get("description", "")).strip(),
        severity=severity,
        source=data["source"],
        filter_fields=dict(data.get("filter", {})),
        window_seconds=int(data.get("window_seconds", 60)),
        aggregate=agg,
    )


def load_from_dir(path: Path) -> list[Rule]:
    """Carrega todos os *.yml/*.yaml do diretorio. Erros viram log.warning + skip."""
    rules: list[Rule] = []
    if not path.is_dir():
        return rules
    for f in sorted(path.glob("*.y*ml")):
        try:
            with f.open() as fp:
                data = yaml.safe_load(fp)
            if not isinstance(data, dict):
                raise ValueError("yaml top-level deve ser um mapping")
            rules.append(parse_rule(data))
        except Exception as e:  # noqa: BLE001
            log.warning("falha ao carregar rule %s: %s", f.name, e)
    return rules


def load_default_rules() -> list[Rule]:
    """Carrega o pacote starter em app/rules/."""
    return load_from_dir(Path(__file__).resolve().parents[2] / "rules")
