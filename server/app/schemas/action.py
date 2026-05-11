import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_id: uuid.UUID
    alert_id: uuid.UUID | None
    action_type: str
    target: str
    reason: str
    status: str
    error_message: str | None
    created_at: datetime
    sent_at: datetime | None
    executed_at: datetime | None
    reverted_at: datetime | None


class ActionUpdate(BaseModel):
    status: Literal["reverted"]
