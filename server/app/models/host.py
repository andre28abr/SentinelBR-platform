import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)

    os_family: Mapped[str | None] = mapped_column(String(50))
    os_distro: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(100))
    kernel: Mapped[str | None] = mapped_column(String(100))
    arch: Mapped[str | None] = mapped_column(String(50))

    # Localizacao fisica/logica do host (DC, sala, rack, etc). Editavel pelo user.
    location: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrollment_token: Mapped[str | None] = mapped_column(String(64), index=True)
    enrollment_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Latest snapshot from heartbeat stats (atualizado a cada heartbeat ~30s)
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv4 ou IPv6
    cpu_count: Mapped[int | None] = mapped_column(Integer)
    load_avg_1m: Mapped[float | None] = mapped_column(Float)
    mem_used_bytes: Mapped[int | None] = mapped_column(BigInteger)
    mem_total_bytes: Mapped[int | None] = mapped_column(BigInteger)
    disk_used_bytes: Mapped[int | None] = mapped_column(BigInteger)
    disk_total_bytes: Mapped[int | None] = mapped_column(BigInteger)
    uptime_seconds: Mapped[int | None] = mapped_column(BigInteger)

    # ClamAV detection (reportado pelo agente no heartbeat)
    clamav_installed: Mapped[bool | None] = mapped_column(Boolean)
    clamav_version: Mapped[str | None] = mapped_column(String(255))
    clamav_db_age_days: Mapped[int | None] = mapped_column(Integer)

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
