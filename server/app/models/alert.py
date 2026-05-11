import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # status: open | acknowledged | resolved
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)

    # campos adicionais do match (source.ip, user.name, etc) — JSON pra evolucao livre
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # dedup_key: hash dos campos do group_by da regra. Permite "atualizar" o alerta
    # ao inves de criar duplicado quando a mesma combinacao continua acontecendo.
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("host_id", "rule_id", "dedup_key", name="uq_alert_host_rule_dedup"),
    )
