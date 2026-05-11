import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class HostPackage(Base):
    """Pacote instalado em um host. Atualizado a cada SubmitInventory.

    Eh um snapshot — pacotes que somem do inventario sao deletados (não viram historico).
    Pra historico de instalacoes/removals, ler audit_logs.
    """

    __tablename__ = "host_packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(255), nullable=False)
    arch: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # apt|dnf|zypper|...

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("host_id", "name", "arch", name="uq_host_package_name_arch"),
    )
