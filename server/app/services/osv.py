"""Cliente HTTP do OSV.dev (Open Source Vulnerabilities) — base aberta agregada
do Google que cobre Debian, Ubuntu, RHEL, Alpine, PyPI, npm, etc.

Vantagens vs NVD:
    - Free, sem auth, sem rate limit chato
    - API batch (1 POST = N pacotes)
    - Ja agrega aliases (CVE-X = GHSA-Y = etc.)

Doc: https://google.github.io/osv.dev/api/
"""

from __future__ import annotations

import dataclasses
import logging

import httpx

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_QUERY_URL = "https://api.osv.dev/v1/query"

log = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True)
class PackageQuery:
    name: str
    version: str
    ecosystem: str  # "Debian:12", "Ubuntu:22.04", "Alpine:v3.19", "Rocky Linux:9"


@dataclasses.dataclass(slots=True)
class Vulnerability:
    cve_id: str          # ID principal (CVE preferido se existir nos aliases)
    summary: str
    severity: str        # critical | high | medium | low | unknown
    cvss_score: float | None
    fixed_version: str | None
    references: list[str]


def os_to_ecosystem(distro: str | None, version: str | None) -> str | None:
    """Mapeia osdetect.OSInfo (distro+version) -> ecosystem string que o OSV usa.

    OSV ecosystems suportados (parcial): https://ossf.github.io/osv-schema/#defined-ecosystems
    """
    if not distro:
        return None
    if not version:
        version = ""
    d = distro.lower()
    if d == "ubuntu":
        return f"Ubuntu:{version}"
    if d == "debian":
        # OSV usa apenas major number (ex: "Debian:12", nao "Debian:12.5")
        major = version.split(".")[0] if version else ""
        return f"Debian:{major}" if major else None
    if d == "rocky":
        major = version.split(".")[0] if version else ""
        return f"Rocky Linux:{major}" if major else None
    if d == "almalinux":
        major = version.split(".")[0] if version else ""
        return f"AlmaLinux:{major}" if major else None
    if d == "rhel":
        major = version.split(".")[0] if version else ""
        return f"Red Hat:{major}" if major else None
    if d == "alpine":
        # Alpine usa "Alpine:vX.Y"
        return f"Alpine:v{version}" if version else None
    if d == "fedora":
        major = version.split(".")[0] if version else ""
        return f"Fedora:{major}" if major else None
    return None


def _pick_severity(cvss_score: float | None) -> str:
    if cvss_score is None:
        return "unknown"
    if cvss_score >= 9.0:
        return "critical"
    if cvss_score >= 7.0:
        return "high"
    if cvss_score >= 4.0:
        return "medium"
    return "low"


def _pick_cvss(vuln_obj: dict) -> float | None:
    """Pega o maior CVSS v3.x score da lista de severities, se houver."""
    best: float | None = None
    for sev in vuln_obj.get("severity", []) or []:
        if sev.get("type", "").startswith("CVSS_V3"):
            try:
                # OSV format: score eh string tipo "CVSS:3.1/AV:N/AC:L/.../I:H/A:H" — precisa parse
                # mas alguns ja vem como float. Tenta float direto primeiro.
                score_str = sev.get("score", "")
                if "/" in score_str:
                    # vetor — pula, complexo demais. Fallback: cvss-via-rating em database_specific.
                    continue
                v = float(score_str)
                if best is None or v > best:
                    best = v
            except (ValueError, TypeError):
                continue
    return best


def _normalize_id(vuln_obj: dict) -> str:
    """Prefere CVE-XXXX se existir nos aliases; senao usa o ID primario."""
    main_id = vuln_obj.get("id", "")
    aliases = vuln_obj.get("aliases", []) or []
    for a in aliases:
        if a.startswith("CVE-"):
            return a
    return main_id


def _normalize_vuln(v: dict) -> Vulnerability:
    cvss = _pick_cvss(v)
    fixed = None
    for affected in v.get("affected", []) or []:
        for r in affected.get("ranges", []) or []:
            for ev in r.get("events", []) or []:
                if "fixed" in ev:
                    fixed = ev["fixed"]
                    break
    refs = [r.get("url", "") for r in (v.get("references") or [])]
    return Vulnerability(
        cve_id=_normalize_id(v),
        summary=(v.get("summary") or v.get("details") or "")[:500],
        severity=_pick_severity(cvss),
        cvss_score=cvss,
        fixed_version=fixed,
        references=[r for r in refs if r],
    )


async def query_batch(queries: list[PackageQuery]) -> dict[str, list[Vulnerability]]:
    """Consulta OSV em batch. Retorna dict {package_name -> list[Vulnerability]}.

    Cada query no batch resulta em N vulns. Combina com outra chamada por vuln pra ter detalhes.
    """
    if not queries:
        return {}

    payload = {
        "queries": [
            {
                "package": {"name": q.name, "ecosystem": q.ecosystem},
                "version": q.version,
            }
            for q in queries
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as cli:
        r = await cli.post(OSV_BATCH_URL, json=payload)
        r.raise_for_status()
        body = r.json()

    # batch retorna so IDs — pra detalhes precisamos chamar /v1/query individualmente.
    # Pra perf, paraleliza.
    out: dict[str, list[Vulnerability]] = {}
    results = body.get("results", [])

    pending: list[tuple[str, str]] = []  # (package_name, vuln_id)
    for q, res in zip(queries, results, strict=True):
        for v in res.get("vulns") or []:
            pending.append((q.name, v["id"]))

    if not pending:
        return out

    async with httpx.AsyncClient(timeout=30.0) as cli:
        import asyncio
        async def fetch(pkg: str, vid: str):
            try:
                r = await cli.post(OSV_QUERY_URL, json={"id": vid})
                r.raise_for_status()
                return pkg, _normalize_vuln(r.json())
            except httpx.HTTPError as e:
                log.warning("OSV detail fetch falhou %s: %s", vid, e)
                return pkg, None

        results_with_detail = await asyncio.gather(*(fetch(p, v) for p, v in pending))

    for pkg, vuln in results_with_detail:
        if vuln is None:
            continue
        out.setdefault(pkg, []).append(vuln)

    return out
