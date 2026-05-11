import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_id: uuid.UUID
    rule_id: str
    rule_name: str
    severity: str
    description: str
    count: int
    first_event_at: datetime
    last_event_at: datetime
    status: str
    context: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "resolved"]
