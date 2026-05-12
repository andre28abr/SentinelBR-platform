"""Testes do /api/v1/docs — serve markdown do diretorio docs/ do repo."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_docs_is_public(client: AsyncClient) -> None:
    """Sem auth — UI carrega antes de logar (visivel ate na LoginPage)."""
    r = await client.get("/api/v1/docs")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    # Deve ter pelo menos os principais (01- visao geral, 18- demo mode)
    slugs = {d["slug"] for d in body}
    assert "visao-geral-modulos" in slugs
    assert "demo-mode" in slugs


@pytest.mark.asyncio
async def test_list_docs_ordered_numerically(client: AsyncClient) -> None:
    r = await client.get("/api/v1/docs")
    assert r.status_code == 200
    orders = [d["order"] for d in r.json()]
    assert orders == sorted(orders), "ordem nao crescente"


@pytest.mark.asyncio
async def test_list_docs_skips_README(client: AsyncClient) -> None:
    r = await client.get("/api/v1/docs")
    slugs = {d["slug"] for d in r.json()}
    # README*.md sao filtrados — sao indice do GitHub, nao do app
    assert "readme" not in slugs
    assert "readme2" not in slugs


@pytest.mark.asyncio
async def test_get_doc_returns_markdown(client: AsyncClient) -> None:
    r = await client.get("/api/v1/docs/demo-mode")
    assert r.status_code == 200
    body = r.json()
    assert body["slug"] == "demo-mode"
    assert body["title"]  # H1 extraido
    assert "# Modo Laboratório" in body["markdown"]


@pytest.mark.asyncio
async def test_get_doc_404_for_unknown(client: AsyncClient) -> None:
    r = await client.get("/api/v1/docs/nao-existe")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_doc_rejects_path_traversal(client: AsyncClient) -> None:
    """Slug deve rejeitar tentativas de path traversal."""
    # Path traversal classicos retornam 404 do roteador OU 404 da validacao slug
    for bad in ["..%2Fpasswd", "../../etc/passwd"]:
        r = await client.get(f"/api/v1/docs/{bad}")
        assert r.status_code == 404
