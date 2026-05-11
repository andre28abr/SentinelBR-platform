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
import re

import httpx
from cvss import CVSS3

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_QUERY_URL = "https://api.osv.dev/v1/query"
OSV_VULN_URL = "https://api.osv.dev/v1/vulns"  # GET /vulns/{id} pra detalhes

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


_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}")


def _pick_cvss(vuln_obj: dict) -> float | None:
    """Pega o maior CVSS v3.x score. OSV armazena como vetor string
    (CVSS:3.1/AV:N/AC:L/...), entao precisamos calcular."""
    best: float | None = None
    for sev in vuln_obj.get("severity", []) or []:
        if not sev.get("type", "").startswith("CVSS_V3"):
            continue
        score_str = sev.get("score", "")
        if not score_str:
            continue
        try:
            if "/" in score_str:
                v = float(CVSS3(score_str).base_score)
            else:
                v = float(score_str)
        except Exception as e:  # noqa: BLE001 (CVSS3 lanca varias excecoes)
            log.debug("cvss parse falhou %r: %s", score_str, e)
            continue
        if best is None or v > best:
            best = v
    return best


def _normalize_id(vuln_obj: dict) -> str:
    """Prefere CVE-XXXX-NNNN. Tenta nos aliases primeiro, depois extrai do ID."""
    aliases = vuln_obj.get("aliases", []) or []
    for a in aliases:
        if a.startswith("CVE-"):
            return a
    # Tenta extrair do proprio ID (ex: "DEBIAN-CVE-2021-23239" -> "CVE-2021-23239")
    main_id = vuln_obj.get("id", "")
    m = _CVE_RE.search(main_id)
    if m:
        return m.group(0)
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
        # OSV nao tem batch pra detalhes — eh GET /v1/vulns/{id} um por um.
        # Limitamos concorrencia pra nao tomar rate limit.
        sem = asyncio.Semaphore(8)

        async def fetch(pkg: str, vid: str):
            async with sem:
                try:
                    r = await cli.get(f"{OSV_VULN_URL}/{vid}")
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
