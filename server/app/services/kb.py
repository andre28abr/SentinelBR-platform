"""Loader da Knowledge Base (MITRE ATT&CK PT-BR + hunting + playbooks).

Conteudo eh estatico em YAML files dentro de app/kb/data/. Loader le tudo
no startup, faz cache em memoria. Atualizacao = redeploy do server (intencional
— conteudo educacional, baixa frequencia de mudanca).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_KB_ROOT = Path(__file__).resolve().parent.parent / "kb" / "data"


def _load_dir(subdir: str) -> list[dict[str, Any]]:
    base = _KB_ROOT / subdir
    if not base.is_dir():
        return []
    items: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.yml")):
        with path.open(encoding="utf-8") as fh:
            items.append(yaml.safe_load(fh))
    return items


@lru_cache(maxsize=1)
def list_techniques() -> list[dict[str, Any]]:
    return _load_dir("techniques")


@lru_cache(maxsize=1)
def list_hunting_queries() -> list[dict[str, Any]]:
    return _load_dir("hunting")


@lru_cache(maxsize=1)
def list_playbooks() -> list[dict[str, Any]]:
    return _load_dir("playbooks")


@lru_cache(maxsize=1)
def _load_action_types() -> dict[str, Any]:
    """Carrega action_types.yml — explicacoes leigas por action_type."""
    path = _KB_ROOT / "action_types.yml"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def get_technique(tid: str) -> dict[str, Any] | None:
    for t in list_techniques():
        if t.get("id") == tid:
            return t
    return None


def explain_rule(rule_id: str) -> dict[str, Any] | None:
    """Dado um rule_id de detection (ex: ssh_brute_force_ip), retorna a tecnica
    MITRE que cobre ele com o summary_simple. None se nao mapeado."""
    for t in list_techniques():
        det = t.get("detection") or {}
        if rule_id in (det.get("rules") or []):
            return t
    return None


def explain_action(action_type: str) -> dict[str, Any] | None:
    """Dado um action_type (block_ip, quarantine_file, etc), retorna explicacao
    leiga. None se action_type desconhecido."""
    action_types = _load_action_types()
    return action_types.get(action_type)
