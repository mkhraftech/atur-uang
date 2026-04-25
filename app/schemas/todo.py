from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class TodoCreate(BaseModel):
    text: str
    remind_at: Optional[datetime] = None
    phone: str


class TodoResponse(BaseModel):
    id: uuid.UUID
    text: str
    remind_at: Optional[datetime]
    is_done: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
