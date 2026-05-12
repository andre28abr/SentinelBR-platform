import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.services.auth import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials, "access")
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="token expirado") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="token invalido") from e

    user_id = uuid.UUID(payload["sub"])
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="usuario nao encontrado ou inativo")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: str):
    """Dependency factory pra restringir endpoint a roles especificos.

    Uso:
        @router.delete("/x", dependencies=[Depends(require_role("admin"))])

    OU como dep injection com Annotated:
        AdminUser = Annotated[User, Depends(require_role("admin"))]
    """
    async def _check(current: CurrentUser) -> User:
        if current.role not in allowed_roles:
            needed = ",".join(allowed_roles)
            raise HTTPException(
                status_code=403,
                detail=f"role '{current.role}' insuficiente (necessario: {needed})",
            )
        return current
    return _check


# Roles padrao em uso: "admin" (full), "operator" (acoes), "viewer" (read-only).
# Ver models/user.py:22 — default eh "admin", users novos via /users criariam
# operator, mas esse endpoint nao existe ainda (single-org admin self-service).
AdminUser = Annotated[User, Depends(require_role("admin"))]
OperatorUser = Annotated[User, Depends(require_role("admin", "operator"))]
