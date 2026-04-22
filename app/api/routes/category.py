from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.category_service import CategoryService
from app.utils.dependency import get_db

router = APIRouter(
    prefix="/api/v1/categories",
    tags=["category"]
)

# sementara hardcode user_id
USER_ID = "550e8400-e29b-41d4-a716-446655440000"


@router.get("")
def get_categories(db: Session = Depends(get_db)):
    return CategoryService.get_all(db, USER_ID)
