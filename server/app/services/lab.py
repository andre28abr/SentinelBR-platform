"""Lab service — wrapper sobre `orb` (OrbStack CLI) pra controlar VMs do
demo via UI.

Modelo de seguranca:
- VM names sao validados contra `^lab-[a-z0-9-]+$` antes de qualquer exec.
- subprocess.exec com argv list (NUNCA shell=True) → sem injecao de shell.
- Timeout em todo comando (orb stop pode travar; nao queremos handler hung).
- Endpoints que chamam essas funcoes ja gateado por `lab_mode=true` no
  router (ver app/api/lab.py).

Por que isso so existe em LAB MODE: orb pode parar/iniciar VMs no host real
do desenvolvedor. Em prod multi-tenant seria caos. lab_mode=true eh opt-in
explicito (env var) com banner gritante na UI.
"""

from __future__ import annotations

import asyncio
import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings

# VM names esperados: lab-debian-11, lab-fedora, lab-vuln, lab-rocky-9, etc.
# Restritivo de proposito — bloqueia "; rm -rf /" e parecidos (mesmo com
# argv list, defesa em camadas).
_VM_NAME_RE = re.compile(r"^lab-[a-z0-9][a-z0-9-]{0,30}[a-z0-9]$")

# Timeout default pra comandos orb. start/stop podem demorar, attack pode
# levar minutos pelo provisionamento — entao usamos limite mais generoso.
_DEFAULT_TIMEOUT_SECONDS = 30
_LONG_TIMEOUT_SECONDS = 300  # attack.sh / up.sh podem ser lentos


class LabError(RuntimeError):
    """Erro generico do lab (orb falhou, VM nao existe, etc)."""


class InvalidVmNameError(LabError):
    """Nome de VM nao bate com `^lab-[a-z0-9-]+$`."""


@dataclass(frozen=True)
class VmInfo:
    """Info estruturada de uma VM, retornada pra UI."""
    name: str
    state: str  # "running" | "stopped" | "starting" | "unknown"
    distro: str  # "debian:11" | "ubuntu:22.04" | etc
    arch: str   # "arm64" | "amd64"


def _validate_vm_name(name: str) -> None:
    """Levanta InvalidVmNameError se name nao bate o regex restritivo."""
    if not _VM_NAME_RE.match(name):
        raise InvalidVmNameError(
            f"VM name invalido: {name!r} (esperado ^lab-[a-z0-9-]+$)"
        )


async def _run_orb(
    *args: str, timeout: int = _DEFAULT_TIMEOUT_SECONDS,  # noqa: ASYNC109
) -> tuple[int, str, str]:
    # ASYNC109: usamos asyncio.wait_for() abaixo (idiomatic pra subprocess),
    # nao precisa de asyncio.timeout context manager.
    """Roda `orb <args...>` e retorna (returncode, stdout, stderr).

    NUNCA usa shell=True — argv eh passado direto. Levanta LabError se
    timeout exceder ou orb nao for encontrado.
    """
    settings = get_settings()
    cmd = [settings.lab_orb_binary, *args]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as e:
        raise LabError(
            f"orb nao encontrado em PATH (configure SENTINELBR_LAB_ORB_BINARY): {e}"
        ) from e

    try:
        stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError as e:
        # mata o processo se ainda estiver vivo — evita zumbi
        try:
            proc.kill()
            await proc.wait()
        except ProcessLookupError:
            pass
        raise LabError(f"timeout ({timeout}s) em: {shlex.join(cmd)}") from e

    return (
        proc.returncode or 0,
        stdout_b.decode("utf-8", errors="replace"),
        stderr_b.decode("utf-8", errors="replace"),
    )


async def list_vms() -> list[VmInfo]:
    """Lista VMs OrbStack com prefixo `lab-`. Pula VMs sem prefixo
    (deixa o usuario com VMs proprias intactas no orb)."""
    rc, stdout, stderr = await _run_orb("list", "--format", "json")
    if rc != 0:
        raise LabError(f"orb list falhou (rc={rc}): {stderr.strip()}")

    try:
        raw = json.loads(stdout) if stdout.strip() else []
    except json.JSONDecodeError as e:
        raise LabError(f"orb list nao retornou JSON valido: {e}") from e

    vms: list[VmInfo] = []
    for entry in raw:
        name = str(entry.get("name", ""))
        if not name.startswith("lab-"):
            continue
        # OrbStack JSON: state pode ser "running" | "stopped". Image string
        # como "debian:11" ou "ubuntu:22.04". Arch como "arm64" / "amd64".
        vms.append(VmInfo(
            name=name,
            state=str(entry.get("state", "unknown")),
            distro=str(entry.get("image", "")),
            arch=str(entry.get("arch", "")),
        ))
    # Ordena por nome pra UI ter ordem estavel.
    vms.sort(key=lambda v: v.name)
    return vms


async def start_vm(name: str) -> None:
    """`orb start <name>`. No-op se ja estiver rodando (orb e idempotente)."""
    _validate_vm_name(name)
    rc, _, stderr = await _run_orb("start", name)
    if rc != 0:
        raise LabError(f"orb start {name} falhou: {stderr.strip()}")


async def stop_vm(name: str) -> None:
    """`orb stop <name>`. No-op se ja estiver parada."""
    _validate_vm_name(name)
    rc, _, stderr = await _run_orb("stop", name)
    if rc != 0:
        raise LabError(f"orb stop {name} falhou: {stderr.strip()}")


def _scripts_dir() -> Path:
    """Resolve LABS_DIR (default: <repo>/samples/labs)."""
    settings = get_settings()
    if settings.lab_scripts_dir:
        return Path(settings.lab_scripts_dir).resolve()
    # Default: server/app/services/lab.py → server/ → repo/ → samples/labs
    return Path(__file__).resolve().parents[3] / "samples" / "labs"


async def attack_vm(name: str) -> str:
    """Re-roda attack.sh pra UMA VM especifica (slug sem o prefixo lab-).

    Ex: name='lab-debian-11' → roda `attack.sh debian-11`.
    Retorna stdout pra UI ver o que aconteceu.
    """
    _validate_vm_name(name)
    distro_slug = name.removeprefix("lab-")  # "debian-11" etc
    scripts_dir = _scripts_dir()
    attack_sh = scripts_dir / "attack.sh"
    if not attack_sh.is_file():
        raise LabError(f"attack.sh nao existe em {scripts_dir}")

    # bash <script> <slug> — argv direto, sem shell.
    proc = await asyncio.create_subprocess_exec(
        "bash", str(attack_sh), distro_slug,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(scripts_dir),
    )
    try:
        stdout_b, _ = await asyncio.wait_for(
            proc.communicate(), timeout=_LONG_TIMEOUT_SECONDS
        )
    except TimeoutError as e:
        try:
            proc.kill()
            await proc.wait()
        except ProcessLookupError:
            pass
        raise LabError(f"attack.sh {distro_slug} timeout (5min)") from e

    output = stdout_b.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        raise LabError(f"attack.sh falhou (rc={proc.returncode}):\n{output}")
    return output
