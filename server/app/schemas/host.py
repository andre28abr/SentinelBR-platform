import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HostCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    hostname: str = Field(min_length=1, max_length=255)


class HostUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    hostname: str | None = Field(default=None, min_length=1, max_length=255)


class HostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    hostname: str
    os_family: str | None
    os_distro: str | None
    os_version: str | None
    status: str
    last_heartbeat: datetime | None
    created_at: datetime
