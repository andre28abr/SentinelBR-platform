from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api import (
    actions,
    agents,
    alerts,
    audit,
    auth,
    clamav,
    docs,
    events,
    fail2ban,
    firewall,
    health,
    hosts,
    kb,
    lab,
    organizations,
    tools,
    vulnerabilities,
    yara,
)
from app.config import get_settings
from app.services.observability import setup_observability
from app.services.ratelimit import limiter, rate_limit_handler


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="SentinelBR — plataforma de segurança para servidores Linux",
        lifespan=lifespan,
    )
    origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
    if not origins:
        raise RuntimeError("SENTINELBR_CORS_ALLOWED_ORIGINS vazio — defina origens explicitas")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,  # cookies httpOnly de refresh dependem disso
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )
    # Rate limit (slowapi) — pra agora protege /auth/login e /agents/enroll
    # via decorator @limiter.limit. Handler 429 retorna detail amigavel.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    # Observabilidade: structlog + X-Request-ID middleware + /metrics Prometheus
    setup_observability(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(hosts.router)
    app.include_router(agents.router)
    app.include_router(events.router)
    app.include_router(alerts.router)
    app.include_router(actions.router)
    app.include_router(audit.router)
    app.include_router(vulnerabilities.router)
    app.include_router(yara.router)
    app.include_router(clamav.router)
    app.include_router(fail2ban.router)
    app.include_router(firewall.router)
    app.include_router(tools.router)
    app.include_router(kb.router)
    app.include_router(organizations.router)
    app.include_router(lab.router)
    app.include_router(docs.router)
    return app


app = create_app()
