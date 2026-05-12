import datetime as dt
import uuid

import jwt
from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.models import Organization, RefreshTokenJti, User
from app.schemas.auth import (
    LoginRequest,
    OrganizationBrief,
    RefreshRequest,
    TokenPair,
    UserResponse,
)
from app.services import audit
from app.services.auth import (
    decode_token,
    hash_password,
    issue_token,
    new_jti,
    verify_password,
)
from app.services.ratelimit import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Refresh token vai em cookie httpOnly — sem JS access, sem XSS exfil.
# samesite=lax: cookie acompanha navigation top-level e same-origin POST,
# bloqueia cross-site POST (CSRF protection basico). Em dev (Vite proxy),
# tudo eh same-origin localhost:5173. Em prod, server e UI no mesmo eTLD+1.
REFRESH_COOKIE_NAME = "sentinelbr_refresh"  # noqa: S105

# Hash dummy gerado UMA vez no import — usado pra fazer bcrypt comparison
# constant-time quando usuario nao existe (anti username enumeration via
# timing). Custo ~100ms igual ao caso real de senha errada.
_DUMMY_BCRYPT = hash_password("dummy_constant_time_check_xxxxxxxxxx")  # noqa: S106


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.refresh_token_days * 24 * 3600,
        httponly=True,
        secure=not settings.debug,  # secure=True em prod (HTTPS), False em dev
        samesite="lax",
        path="/api/v1/auth",  # so envia em rotas de auth — minimiza superficie
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/v1/auth",
        httponly=True,
        samesite="lax",
    )


@router.post("/login", response_model=TokenPair)
@limiter.limit("10/minute")
async def login(
    payload: LoginRequest, request: Request, response: Response, db: DbSession,
) -> TokenPair:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Anti username enumeration: sempre rodar verify_password (mesmo com
    # user=None usando hash dummy) pra ter timing constante. Sem isso,
    # atacante diferencia "user nao existe" vs "user existe mas senha
    # errada" pelo tempo de resposta (~5ms vs ~100ms).
    password_ok = verify_password(
        payload.password,
        user.password_hash if user is not None else _DUMMY_BCRYPT,
    )
    if user is None or not password_ok:
        await audit.log_action(
            db,
            action="login_failed",
            actor_email=payload.email[:255],  # truncate anti log pollution
            request=request,
            success=False,
            details={"reason": "wrong_password_or_user_not_found"},
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="email ou senha incorretos")

    if not user.is_active:
        await audit.log_action(
            db,
            action="login_failed",
            actor=user,
            request=request,
            success=False,
            details={"reason": "user_inactive"},
        )
        await db.commit()
        raise HTTPException(status_code=403, detail="usuario inativo")

    # Se org_slug foi informado, valida membership. No MVP cada user pertence a
    # 1 org, entao isso eh basicamente double-check "estou logando no tenant certo?"
    if payload.org_slug:
        from app.models import Organization
        org = await db.get(Organization, user.org_id)
        if org is None or org.slug != payload.org_slug:
            await audit.log_action(
                db,
                action="login_failed",
                actor=user,
                request=request,
                success=False,
                details={"reason": "org_slug_mismatch", "tried_org": payload.org_slug},
            )
            await db.commit()
            raise HTTPException(
                status_code=401, detail="organizacao nao bate com a conta",
            )

    await audit.log_action(db, action="login_success", actor=user, request=request)

    refresh_token, _ = await _emit_refresh(db, user.id)
    _set_refresh_cookie(response, refresh_token)
    await db.commit()

    return TokenPair(
        access_token=issue_token(str(user.id), "access"),
        # refresh_token tambem retornado no body por back-compat (CLI tools,
        # mobile). Em prod considerar remover apos migracao do frontend.
        refresh_token=refresh_token,
    )


async def _emit_refresh(db, user_id: uuid.UUID) -> tuple[str, str]:
    """Emite refresh token novo + persiste jti na tabela. Retorna (token, jti)."""
    settings = get_settings()
    jti = new_jti()
    token = issue_token(str(user_id), "refresh", jti=jti)
    expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(days=settings.refresh_token_days)
    db.add(RefreshTokenJti(jti=jti, user_id=user_id, expires_at=expires_at))
    return token, jti


async def _revoke_jti(db, jti: str) -> None:
    """Marca jti como revoked. No-op se jti nao existe (token velho pre-rotation)."""
    row = await db.get(RefreshTokenJti, jti)
    if row is not None and row.revoked_at is None:
        row.revoked_at = dt.datetime.now(dt.UTC)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("30/minute")
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    payload: RefreshRequest | None = None,
    sentinelbr_refresh: str | None = Cookie(default=None),
) -> TokenPair:
    """Refresh aceita token via cookie httpOnly OU body (back-compat).

    Cookie tem prioridade — frontend novo nao envia body.

    Rotation: ao validar o refresh, marcamos o jti como revoked e emitimos
    um NOVO refresh com novo jti. Se o token vazar e atacante usar antes
    do user, o user vai receber 401 no proximo refresh — sinal claro de
    comprometimento. Refresh sem jti (tokens pre-rotation) sao aceitos
    uma vez e migrados.
    """
    refresh_token = sentinelbr_refresh
    if refresh_token is None and payload is not None:
        refresh_token = payload.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=401, detail="refresh token ausente")

    try:
        decoded = decode_token(refresh_token, "refresh")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="refresh token invalido") from e

    user_id = uuid.UUID(decoded["sub"])
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="usuario invalido")

    # Rotation: valida jti ativo (se token foi emitido com a infra nova).
    old_jti = decoded.get("jti")
    if old_jti is not None:
        existing = await db.get(RefreshTokenJti, old_jti)
        if existing is None or existing.revoked_at is not None:
            await audit.log_action(
                db, action="refresh_token_reuse_attempt", actor=user, request=request,
                success=False, details={"jti": old_jti},
            )
            await db.commit()
            raise HTTPException(
                status_code=401, detail="refresh token revogado ou reutilizado",
            )
        # Marca o atual como revoked — proximo uso desse jti vai falhar.
        existing.revoked_at = dt.datetime.now(dt.UTC)

    new_refresh, _ = await _emit_refresh(db, user.id)
    _set_refresh_cookie(response, new_refresh)
    await db.commit()

    return TokenPair(
        access_token=issue_token(str(user.id), "access"),
        refresh_token=new_refresh,
    )


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    db: DbSession,
    sentinelbr_refresh: str | None = Cookie(default=None),
    payload: RefreshRequest | None = None,
) -> None:
    """Apaga cookie + revoga jti se possivel. Idempotente — 204 sempre."""
    refresh_token = sentinelbr_refresh
    if refresh_token is None and payload is not None:
        refresh_token = payload.refresh_token
    if refresh_token:
        try:
            decoded = decode_token(refresh_token, "refresh")
            jti = decoded.get("jti")
            if jti:
                await _revoke_jti(db, jti)
                await db.commit()
        except jwt.InvalidTokenError:
            pass  # token invalido = nada a revogar
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(current: CurrentUser, db: DbSession) -> UserResponse:
    org = await db.get(Organization, current.org_id)
    resp = UserResponse.model_validate(current)
    if org is not None:
        resp.org = OrganizationBrief.model_validate(org)
    return resp
