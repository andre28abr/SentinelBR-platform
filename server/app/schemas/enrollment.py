import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EnrollmentTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    install_command: str


class AgentOSInfo(BaseModel):
    family: str
    distro: str
    version: str | None = None
    arch: str | None = None
    kernel: str | None = None
    package_manager: str | None = None
    init_system: str | None = None
    firewall_tool: str | None = None
    mac_system: str | None = None


class AgentEnrollRequest(BaseModel):
    token: str = Field(min_length=10)
    hostname: str = Field(min_length=1, max_length=255)
    os: AgentOSInfo


class AgentEnrollResponse(BaseModel):
    host_id: uuid.UUID
    ca_cert_pem: str
    client_cert_pem: str
    client_key_pem: str
    grpc_endpoint: str
