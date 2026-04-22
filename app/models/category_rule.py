from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    user_id = Column(UUID(as_uuid=True), nullable=True)
    category_id = Column(UUID(as_uuid=True))
    keyword = Column(String(100))
    created_at = Column(TIMESTAMP)