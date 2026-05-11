import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HostCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    hostname: str = Field(min_length=1, max_length=255)


class HostUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    hostname: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)


class HostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    hostname: str
    os_family: str | None
    os_distro: str | None
    os_version: str | None
    kernel: str | None = None
    arch: str | None = None
    location: str | None = None
    status: str
    last_heartbeat: datetime | None
    created_at: datetime
    # Stats snapshot (atualizado a cada heartbeat)
    ip_address: str | None = None
    cpu_count: int | None = None
    load_avg_1m: float | None = None
    mem_used_bytes: int | None = None
    mem_total_bytes: int | None = None
    disk_used_bytes: int | None = None
    disk_total_bytes: int | None = None
    uptime_seconds: int | None = None
    clamav_installed: bool | None = None
    clamav_version: str | None = None
    clamav_db_age_days: int | None = None
