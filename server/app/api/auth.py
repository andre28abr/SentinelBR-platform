import uuid

import jwt
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair, UserResponse
from app.services import audit
from app.services.auth import decode_token, issue_token, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenPair:
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

    await audit.log_action(db, action="login_success", actor=user, request=request)
    await db.commit()

    return TokenPair(
        access_token=issue_token(str(user.id), "access"),
        refresh_token=issue_token(str(user.id), "refresh"),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    try:
        decoded = decode_token(payload.refresh_token, "refresh")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="refresh token invalido") from e

    user_id = uuid.UUID(decoded["sub"])
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="usuario invalido")

    return TokenPair(
        access_token=issue_token(str(user.id), "access"),
        refresh_token=issue_token(str(user.id), "refresh"),
    )


@router.get("/me", response_model=UserResponse)
async def me(current: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current)
