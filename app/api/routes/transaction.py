from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService
from app.utils.dependency import get_db

router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["transaction"]
)

# sementara hardcode user_id
USER_ID = "550e8400-e29b-41d4-a716-446655440000"


@router.post("")
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    return TransactionService.create_transaction(db, None, data)


@router.get("")
def get_transactions(db: Session = Depends(get_db)):
    return TransactionService.get_all(db, USER_ID)


@router.get("/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    return TransactionService.get_by_id(db, USER_ID, transaction_id)


@router.put("/{transaction_id}")
def update_transaction(transaction_id: str, data: TransactionCreate, db: Session = Depends(get_db)):
    return TransactionService.update(db, None, transaction_id, data)


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: str, db: Session = Depends(get_db)):
    return TransactionService.delete(db, None, transaction_id)