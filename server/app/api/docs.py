"""REST endpoints pra servir os docs em markdown que ficam em /docs do repo.

Carregados em memoria no startup e servidos pra UI renderizar com
react-markdown. Lista ordenada pelo prefixo numerico (01-, 02-, ..., 18-).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/docs", tags=["docs"])

# Path: server/app/api/docs.py → repo root → docs/
_DOCS_DIR = Path(__file__).resolve().parents[3] / "docs"

# Slug deve casar somente com nomes de arquivo seguros — sem path traversal.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")


class DocSummary(BaseModel):
    """Item da lista — slug pra montar URL + titulo extraido do H1."""

    slug: str
    title: str
    order: int  # ordem numerica extraida do prefixo (01- → 1, 18- → 18)


class DocContent(BaseModel):
    slug: str
    title: str
    markdown: str


def _slug_from_filename(name: str) -> str:
    """01-visao-geral-modulos.md → visao-geral-modulos."""
    stem = name.removesuffix(".md")
    # Remove prefixo numerico tipo "01-"
    return re.sub(r"^\d+-", "", stem).lower()


def _order_from_filename(name: str) -> int:
    """Extrai 1 de '01-visao-geral.md', 99 pra arquivos sem prefixo."""
    m = re.match(r"^(\d+)-", name)
    return int(m.group(1)) if m else 999


def _title_from_markdown(md: str, fallback: str) -> str:
    """Extrai 1o H1 (# Titulo) do markdown — eh oque a UI mostra na sidebar."""
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


@lru_cache(maxsize=1)
def _index() -> list[DocSummary]:
    """Lista ordenada de docs disponiveis, lida 1x e cacheada."""
    if not _DOCS_DIR.is_dir():
        return []
    items: list[DocSummary] = []
    for path in sorted(_DOCS_DIR.glob("*.md")):
        # README*.md sao indices do GitHub, pulamos do app pra nao confundir
        # (a sidebar do app ja eh o "indice").
        if path.stem.upper().startswith("README"):
            continue
        slug = _slug_from_filename(path.name)
        if not _SLUG_RE.match(slug):
            continue
        try:
            md = path.read_text(encoding="utf-8")
        except OSError:
            continue
        items.append(DocSummary(
            slug=slug,
            title=_title_from_markdown(md, fallback=slug),
            order=_order_from_filename(path.name),
        ))
    items.sort(key=lambda d: (d.order, d.slug))
    return items


@lru_cache(maxsize=64)
def _load_doc(slug: str) -> DocContent | None:
    """Carrega 1 doc pelo slug. None se nao existe."""
    if not _SLUG_RE.match(slug):
        return None
    if not _DOCS_DIR.is_dir():
        return None
    for path in _DOCS_DIR.glob("*.md"):
        if _slug_from_filename(path.name) == slug:
            try:
                md = path.read_text(encoding="utf-8")
            except OSError:
                return None
            return DocContent(
                slug=slug,
                title=_title_from_markdown(md, fallback=slug),
                markdown=md,
            )
    return None


@router.get("", response_model=list[DocSummary])
async def list_docs() -> list[DocSummary]:
    """Indice pra sidebar do /docs no app. Publico (sem auth)."""
    return _index()


@router.get("/{slug}", response_model=DocContent)
async def get_doc(slug: str) -> DocContent:
    """Retorna markdown bruto de UM doc pelo slug. Publico (sem auth)."""
    doc = _load_doc(slug)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"doc '{slug}' nao encontrado")
    return doc
