"""Rate limit configuration via slowapi.

Storage padrao eh in-memory por processo. Em prod com multiplos workers,
considerar usar Redis pra estado compartilhado:
    Limiter(key_func=get_remote_address, storage_uri="redis://...")
Por ora, slowapi default (memory:// per-process) — basta pra mitigar
brute-force basico em /auth/login e /agents/enroll.
"""

from __future__ import annotations

import sys

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Em ambiente de teste (pytest carregado), desativa rate limit completamente
# pra testes de auth nao falharem ao fazer N logins consecutivos.
# Em prod, sys.modules nao tem pytest, entao limites ficam ativos.
_TESTING = "pytest" in sys.modules

limiter = Limiter(
    key_func=get_remote_address,
    enabled=not _TESTING,
)


async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom 429 handler com mensagem em PT-BR.

    Assinatura aceita Exception (nao RateLimitExceeded direto) pra satisfazer
    o tipo do FastAPI exception_handlers (que espera Exception).
    """
    if not isinstance(exc, RateLimitExceeded):
        raise exc
    return JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"limite de {exc.detail} atingido. Tente novamente em alguns segundos."
            ),
        },
        headers={"Retry-After": "60"},
    )
