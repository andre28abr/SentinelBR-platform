from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    source: str
    severity: str
    raw: str
    fields: dict[str, str]
