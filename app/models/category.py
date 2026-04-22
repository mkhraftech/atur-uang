from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(50))
    type = Column(String(10))  # income / expense
    created_at = Column(TIMESTAMP)