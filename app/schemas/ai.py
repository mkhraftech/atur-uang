from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
import datetime

class ReceiptData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: Optional[float] = None
    transaction_date: Optional[datetime.date] = Field(None, alias="date")
    merchant: Optional[str] = None
    description: Optional[str] = None
    category_suggestion: Optional[str] = None
    currency: Optional[str] = "IDR"
    items: Optional[List[str]] = []

