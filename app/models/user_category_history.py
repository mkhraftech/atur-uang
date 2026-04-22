from sqlalchemy import Column, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class UserCategoryHistory(Base):
    __tablename__ = "user_category_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    user_id = Column(UUID(as_uuid=True))
    category_id = Column(UUID(as_uuid=True))
    description = Column(Text)
    usage_count = Column(Integer, default=1)
    last_used = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())