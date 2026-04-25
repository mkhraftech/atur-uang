from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.dependency import get_db
from app.services.transaction_service import TransactionService
from app.core.logger import logger

router = APIRouter(
    prefix="/api/v1/insights",
    tags=["Insights"]
)

USER_ID = "550e8400-e29b-41d4-a716-446655440000"


@router.get("")
def get_insight(db: Session = Depends(get_db)):
    logger.info("Generating insights")
    return TransactionService.generate_insight(db, USER_ID)