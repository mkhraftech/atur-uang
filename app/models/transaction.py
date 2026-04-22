from sqlalchemy import Column, String, Date, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    # account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"))
    user_id = Column(UUID(as_uuid=True))
    account_id = Column(UUID(as_uuid=True))
    amount = Column(Numeric, nullable=False)
    type = Column(String(10))  # income / expense
    description = Column(String)
    transaction_date = Column(Date)
    created_at = Column(TIMESTAMP)