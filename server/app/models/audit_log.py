import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AuditLog(Base):
    """Registro imutavel de cada operacao relevante na plataforma.

    Atende LGPD Art. 37 (registro de operacoes de tratamento). Append-only,
    sem update — apenas insert e SELECT. Retencao configuravel via worker
    Celery (cleanup_old_audit_logs).
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Quem fez a acao. actor_user_id eh nullable porque login_failed nao tem user logado.
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_email: Mapped[str | None] = mapped_column(String(255))  # snapshot pra sobreviver a delete

    # O que foi feito.
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # ex: login_success, login_failed, host_created, host_deleted, alert_acknowledged,
    #     action_reverted, compliance_report_generated, etc.

    # Em que (target_type='host', target_id=UUID; ou target_type='alert', etc.)
    target_type: Mapped[str | None] = mapped_column(String(50))
    target_id: Mapped[str | None] = mapped_column(String(100))  # str pra aceitar UUID ou outro ID

    # Detalhes em JSON (request body sanitizado, contexto, motivo).
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Origem da requisicao.
    ip_address: Mapped[str | None] = mapped_column(String(50))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    # Resultado.
    success: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
