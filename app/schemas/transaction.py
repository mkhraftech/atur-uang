from pydantic import BaseModel
from datetime import date
from uuid import UUID
from typing import List, Optional

class TransactionCreate(BaseModel):
    account_id: UUID
    amount: float
    type: str
    description: str
    transaction_date: date
    category_ids: List[UUID]
    category_suggestion: Optional[str] = None


class TransactionResponse(BaseModel):
    id: UUID
    account_id: UUID
    amount: float
    type: str
    description: str
    transaction_date: date

    class Config:
        from_attributes = True