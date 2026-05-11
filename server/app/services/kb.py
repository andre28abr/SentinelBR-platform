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


def get_technique(tid: str) -> dict[str, Any] | None:
    for t in list_techniques():
        if t.get("id") == tid:
            return t
    return None
