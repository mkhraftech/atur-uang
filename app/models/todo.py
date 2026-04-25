from sqlalchemy import Column, String, Boolean, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
from app.core.database import Base


class Todo(Base):
    __tablename__ = "todos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    phone = Column(String(20), nullable=False)          # nomor WA untuk kirim reminder
    text = Column(Text, nullable=False)                 # isi todo / reminder
    remind_at = Column(TIMESTAMP(timezone=True), nullable=True)  # None = todo biasa
    is_done = Column(Boolean, default=False)
    is_reminded = Column(Boolean, default=False)        # sudah dikirimi notif?
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
