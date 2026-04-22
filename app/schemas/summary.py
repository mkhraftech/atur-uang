from pydantic import BaseModel
from typing import List

class SummaryResponse(BaseModel):
    total_expense: float


class CategorySummary(BaseModel):
    category: str
    total: float


class CategorySummaryResponse(BaseModel):
    data: List[CategorySummary]