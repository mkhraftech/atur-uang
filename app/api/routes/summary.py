from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.dependency import get_db
from app.services.transaction_service import TransactionService

router = APIRouter(
    prefix="/api/v1/summary",
    tags=["Summary"]
)

USER_ID = "550e8400-e29b-41d4-a716-446655440000"


@router.get("")
def get_summary(db: Session = Depends(get_db)):
    return TransactionService.get_summary(db, USER_ID)


@router.get("/by-category")
def by_category(db: Session = Depends(get_db)):
    return TransactionService.get_by_category(db, USER_ID)