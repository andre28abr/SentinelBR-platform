from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    actions,
    agents,
    alerts,
    audit,
    auth,
    events,
    health,
    hosts,
    kb,
    organizations,
    vulnerabilities,
    yara,
)
from app.config import get_settings


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
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
    app.include_router(kb.router)
    app.include_router(organizations.router)
    return app


app = create_app()
