from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.category_rule import CategoryRule
from app.models.user_category_history import UserCategoryHistory
from app.core.logger import logger

class CategorizationService:

    # 🔍 DETECT CATEGORY (SMART ORDER)
    @staticmethod
    def detect_category(db: Session, user_id, description: str, ai_suggestion: str = None):
        if not description:
            return None

        desc = description.lower()

        # 1️⃣ PRIORITAS: USER HISTORY
        history = db.query(UserCategoryHistory)\
            .filter(
                UserCategoryHistory.user_id == user_id,
                func.lower(UserCategoryHistory.description) == desc
            )\
            .order_by(UserCategoryHistory.usage_count.desc())\
            .first()

        if history:
            return history.category_id

        # 2️⃣ KEYWORD RULES
        rules = db.query(CategoryRule)\
            .filter(
                (CategoryRule.user_id == user_id) |
                (CategoryRule.user_id == None)
            ).all()

        for rule in rules:
            if rule.keyword.lower() in desc:
                return rule.category_id

        # 3️⃣ AI SUGGESTION MAPPING (FALLBACK)
        if ai_suggestion:
            suggestion = ai_suggestion.lower()
            
            # Mapping sederhana Inggris -> Indonesia untuk kompatibilitas
            mapping = {
                "food": "Jajan",
                "shopping": "Impulsif",
                "transport": "Transport",
                "bills": "Wajib",
                "health": "Kebutuhan Pokok",
                "groceries": "Kebutuhan Pokok"
            }
            
            target_name = mapping.get(suggestion, ai_suggestion)
            
            from app.models.category import Category
            category = db.query(Category)\
                .filter(func.lower(Category.name) == target_name.lower())\
                .first()
            
            if category:
                return category.id

        # 4️⃣ FALLBACK
        logger.warning(f"No category found for description: {description}")
        return None

    # 🧠 LEARNING (SAVE / UPDATE HISTORY)
    @staticmethod
    def learn(db: Session, user_id, description: str, category_id):
        desc = description.lower()

        existing = db.query(UserCategoryHistory)\
            .filter(
                UserCategoryHistory.user_id == user_id,
                func.lower(UserCategoryHistory.description) == desc
            ).first()

        if existing:
            existing.usage_count += 1
        else:
            new_data = UserCategoryHistory(
                user_id=user_id,
                description=desc,
                category_id=category_id
            )
            db.add(new_data)

        db.commit()