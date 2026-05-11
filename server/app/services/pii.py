"""Mascaramento de PII pra atender LGPD Art. 6 (minimizacao) na exibicao.

Aplicavel quando o consumidor tem permissao limitada ou quer relatorio sanitizado.
Mascaramento eh aplicado APENAS no display — dado original fica em Loki/DB pra
forensics. Mascaras determinNot deterministicas pra mesma entrada.

Heuristicas reconhecidas:
    - emails               -> u***@d***.com
    - IPs v4               -> 203.0.113.x
    - usernames numericos  -> mantido (nao eh PII)
    - CPF (xxx.xxx.xxx-xx) -> ***.***.***-**
"""

from __future__ import annotations

import re
from typing import Any

_EMAIL_RE = re.compile(
    r"([A-Za-z0-9._%+-])([A-Za-z0-9._%+-]*)@([A-Za-z0-9.-])([A-Za-z0-9.-]*)\.(\w+)"
)
_IPV4_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3})\.(\d{1,3})\b")
_CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")


def mask_email(s: str) -> str:
    return _EMAIL_RE.sub(lambda m: f"{m.group(1)}***@{m.group(3)}***.{m.group(5)}", s)


def mask_ipv4(s: str) -> str:
    return _IPV4_RE.sub(lambda m: f"{m.group(1)}.x", s)


def mask_cpf(s: str) -> str:
    return _CPF_RE.sub("***.***.***-**", s)


def mask_string(s: str) -> str:
    """Aplica todas as mascaras em uma string."""
    if not s:
        return s
    return mask_cpf(mask_email(mask_ipv4(s)))


def mask_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Mascaramento recursivo em dict (string values + nested dicts/lists).

    Chaves NAO sao mascaradas (sao schemas, nao PII).
    """
    out: dict[str, Any] = {}
    for k, v in d.items():
        out[k] = _mask_any(v)
    return out


def _mask_any(v: Any) -> Any:
    if isinstance(v, str):
        return mask_string(v)
    if isinstance(v, dict):
        return mask_dict(v)
    if isinstance(v, list):
        return [_mask_any(x) for x in v]
    return v
