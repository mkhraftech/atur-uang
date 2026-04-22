from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    # category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    transaction_id = Column(UUID(as_uuid=True))
    category_id = Column(UUID(as_uuid=True))