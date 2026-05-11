import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Organization(Base):
    """Tenant raiz no SentinelBR. Todo recurso (hosts, alerts, audit) pertence
    a exatamente uma Organization. Isolamento eh feito por filtro nos endpoints
    REST (tenant-aware queries).

    Slug eh um identificador human-friendly (ex: "acme-corp") usado em URLs e
    exibicao. Imutavel apos criacao.
    """

    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
