import uuid

import jwt
from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.config import get_settings
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserResponse
from app.services import audit
from app.services.auth import decode_token, issue_token, verify_password
from app.services.ratelimit import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Refresh token vai em cookie httpOnly — sem JS access, sem XSS exfil.
# samesite=lax: cookie acompanha navigation top-level e same-origin POST,
# bloqueia cross-site POST (CSRF protection basico). Em dev (Vite proxy),
# tudo eh same-origin localhost:5173. Em prod, server e UI no mesmo eTLD+1.
REFRESH_COOKIE_NAME = "sentinelbr_refresh"  # noqa: S105


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

    if user is None or not verify_password(payload.password, user.password_hash):
        await audit.log_action(
            db,
            action="login_failed",
            actor_email=payload.email,
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
    await db.commit()

    refresh_token = issue_token(str(user.id), "refresh")
    _set_refresh_cookie(response, refresh_token)

    return TokenPair(
        access_token=issue_token(str(user.id), "access"),
        # refresh_token tambem retornado no body por back-compat (CLI tools,
        # mobile). Em prod considerar remover apos migracao do frontend.
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    response: Response,
    db: DbSession,
    payload: RefreshRequest | None = None,
    sentinelbr_refresh: str | None = Cookie(default=None),
) -> TokenPair:
    """Refresh aceita token via cookie httpOnly OU body (back-compat).

    Cookie tem prioridade — frontend novo nao envia body.
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

    new_refresh = issue_token(str(user.id), "refresh")
    _set_refresh_cookie(response, new_refresh)

    return TokenPair(
        access_token=issue_token(str(user.id), "access"),
        refresh_token=new_refresh,
    )


@router.post("/logout", status_code=204)
async def logout(response: Response) -> None:
    """Apaga o cookie de refresh. Frontend tambem deve limpar acessToken local."""
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(current: CurrentUser, db: DbSession) -> UserResponse:
    from app.models import Organization
    from app.schemas.auth import OrganizationBrief

    org = await db.get(Organization, current.org_id)
    resp = UserResponse.model_validate(current)
    if org is not None:
        resp.org = OrganizationBrief.model_validate(org)
    return resp
