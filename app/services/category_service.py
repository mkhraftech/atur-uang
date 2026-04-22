from app.services.categorization_service import CategorizationService
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
import uuid


class CategoryService:

    # 📋 GET ALL (with optional filter later)
    @staticmethod
    def get_all(db: Session, user_id):
        return CategoryRepository.get_all(db, user_id)
