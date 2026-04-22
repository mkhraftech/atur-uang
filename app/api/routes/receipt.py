from fastapi import APIRouter, UploadFile, File, Depends
from app.services.receipt_service import process_receipt
from app.utils.dependency import get_db
from sqlalchemy.orm import Session


router = APIRouter()

@router.post("/api/v1/transaction/receipt")
async def upload_receipt(
    file: UploadFile = File(...),
    user="550e8400-e29b-41d4-a716-446655440000",
    db: Session = Depends(get_db)
    # user=Depends(get_current_user)  # optional
):
    result = await process_receipt(db, file, user)
    return result