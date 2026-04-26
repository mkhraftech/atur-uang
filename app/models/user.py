from sqlalchemy import Column, String, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)
    name = Column(String(255))
    google_id = Column(String(255), unique=True, nullable=False)
    picture = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    timezone = Column(String(50), default="Asia/Jakarta")
    created_at = Column(TIMESTAMP, server_default=func.now())

