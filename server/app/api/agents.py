"""Endpoints publicos consumidos pelo agente (sem auth — autorizacao por enrollment token)."""

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.config import get_settings
from app.schemas.enrollment import AgentEnrollRequest, AgentEnrollResponse
from app.services import enrollment
from app.services.ca import get_ca_cert_pem, sign_client_cert

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/enroll", response_model=AgentEnrollResponse)
async def enroll(payload: AgentEnrollRequest, db: DbSession) -> AgentEnrollResponse:
    host = await enrollment.validate_and_consume(db, payload.token)
    if host is None:
        raise HTTPException(status_code=401, detail="enrollment token invalido ou expirado")

    host.os_family = payload.os.family
    host.os_distro = payload.os.distro
    host.os_version = payload.os.version
    host.kernel = payload.os.kernel
    host.arch = payload.os.arch
    if not host.hostname:
        host.hostname = payload.hostname
    await db.commit()
    await db.refresh(host)

    bundle = sign_client_cert(str(host.id))
    settings = get_settings()

    return AgentEnrollResponse(
        host_id=host.id,
        ca_cert_pem=get_ca_cert_pem().decode(),
        client_cert_pem=bundle.cert_pem.decode(),
        client_key_pem=bundle.key_pem.decode(),
        grpc_endpoint=settings.grpc_public_endpoint,
    )
