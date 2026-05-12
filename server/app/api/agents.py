"""Endpoints publicos consumidos pelo agente (sem auth — autorizacao por enrollment token)."""

from fastapi import APIRouter, HTTPException, Request, Response

from app.api.deps import DbSession
from app.config import get_settings
from app.schemas.enrollment import AgentEnrollRequest, AgentEnrollResponse
from app.services import audit, enrollment
from app.services.ca import get_ca_cert_pem, sign_client_cert
from app.services.ratelimit import limiter

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/enroll", response_model=AgentEnrollResponse)
@limiter.limit("20/minute")
async def enroll(
    payload: AgentEnrollRequest, request: Request, response: Response, db: DbSession,
) -> AgentEnrollResponse:
    host = await enrollment.validate_and_consume(db, payload.token)
    if host is None:
        # Audit failure pra detectar enumeracao de tokens / brute-force.
        await audit.log_action(
            db, action="enrollment_failed", request=request, success=False,
            details={"hostname_claim": payload.hostname},
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="enrollment token invalido ou expirado")

    host.os_family = payload.os.family
    host.os_distro = payload.os.distro
    host.os_version = payload.os.version
    host.kernel = payload.os.kernel
    host.arch = payload.os.arch
    if not host.hostname:
        host.hostname = payload.hostname
    await audit.log_action(
        db, action="enrollment_success", request=request,
        target_type="host", target_id=host.id,
        details={"hostname": host.hostname, "os": payload.os.distro},
    )
    await db.commit()
    await db.refresh(host)

    bundle = sign_client_cert(str(host.id))
    settings = get_settings()

    # client_key_pem eh sensivel (chave privada) — proibe cache em proxy/CDN.
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return AgentEnrollResponse(
        host_id=host.id,
        ca_cert_pem=get_ca_cert_pem().decode(),
        client_cert_pem=bundle.cert_pem.decode(),
        client_key_pem=bundle.key_pem.decode(),
        grpc_endpoint=settings.grpc_public_endpoint,
    )
