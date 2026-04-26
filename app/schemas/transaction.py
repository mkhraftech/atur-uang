from pydantic import BaseModel
from datetime import date
from datetime import datetime
from uuid import UUID
from typing import List, Optional

class TransactionCreate(BaseModel):
    account_id: UUID
    amount: float
    type: str
    description: str
    transaction_date: Optional[datetime] = None
    category_ids: List[UUID]
    category_suggestion: Optional[str] = None