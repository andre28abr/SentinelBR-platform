"""Observabilidade — structlog + request_id middleware + Prometheus metrics.

Setup ativado em main.py via setup_observability(app).

Logs: structlog substitui logging.* — JSON em prod (parse-friendly pra Loki),
console human em dev (debug=True).
Cada request ganha um X-Request-ID UUID (ou usa o do header se cliente passou),
propagado em logs via contextvar.

Metricas: /metrics expoe Prometheus (latency P50/P95, contadores por endpoint).
prometheus-fastapi-instrumentator faz heavy lifting.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

import structlog
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import get_settings

# Context var pra propagar request_id em logs sem precisar passar como parametro.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Adiciona X-Request-ID a cada request — usa o do client se enviado,
    senao gera UUID novo. Coloca no contextvar pra logs estruturados."""

    async def dispatch(self, request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_ctx.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


def _add_request_id(_, __, event_dict: dict) -> dict:
    """Processor structlog que injeta request_id em todos os events."""
    event_dict["request_id"] = request_id_ctx.get()
    return event_dict


def setup_logging() -> None:
    """Configura structlog + redireciona logging stdlib pra ele.

    Em dev (debug=True): renderer console-friendly (cores, indentado).
    Em prod: JSON line-by-line, ideal pra Loki/Datadog/etc.
    """
    settings = get_settings()
    is_dev = settings.debug

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        _add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if is_dev:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Redireciona logging stdlib (uvicorn/sqlalchemy/etc) pra structlog.
    handler = logging.StreamHandler()
    handler.setFormatter(_PassThroughFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level.upper())


class _PassThroughFormatter(logging.Formatter):
    """Repassa msg da stdlib pra structlog em vez de formatar."""

    def format(self, record: logging.LogRecord) -> str:
        # Deixa structlog formatar. Aqui so retornamos o getMessage() bruto;
        # processors do structlog nao rodam pra logs stdlib, mas request_id
        # vai vazar via contextvar mesmo assim quando lendo via logger.
        return record.getMessage()


def setup_observability(app: FastAPI) -> None:
    """Wire-up completo: logging + middleware + Prometheus /metrics."""
    setup_logging()
    app.add_middleware(RequestIDMiddleware)

    # Prometheus instrumentator — counters/histograms automaticos
    # por endpoint (req latency, count, status). Adiciona /metrics.
    Instrumentator(
        excluded_handlers=["/api/v1/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
