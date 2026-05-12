"""Tabela de JTIs de refresh tokens — suporte a rotation/revocation.

Sem isso, refresh tokens stateless (JWT puro) sao validos ate exp (7 dias)
mesmo se vazarem. Com a tabela:
  - /login: emite refresh com novo jti, persiste na tabela ativo
  - /refresh: valida jti existe + nao revoked, marca como revoked, emite novo
    com novo jti (rotation)
  - /logout: revoga jti corrente
  - cron diario: limpa rows com expires_at < now()
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RefreshTokenJti(Base):
    __tablename__ = "refresh_token_jtis"

    # jti como primary key — UUID hex (32 chars, 128 bits randomicos via secrets).
    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    # exp do JWT — apos esse instante, row pode ser GC'd.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True,
    )
    # Quando setado, marca o token como revogado (rotation ou logout).
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
