from app.services.categorization_service import CategorizationService
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction
from app.models.transaction_category import TransactionCategory
from app.models.category import Category
from app.repositories.transaction_repository import TransactionRepository
import uuid
from app.core.logger import logger
from datetime import date


class TransactionService:

    # ➕ CREATE
    @staticmethod
    def create_transaction(db: Session, user_id, data):
        
        # AUTO DETECT kalau kosong
        if not data.category_ids:
            detected = CategorizationService.detect_category(
                db, user_id, data.description, data.category_suggestion
            )

            if detected:
                data.category_ids = [detected]
            
            # FALLBACK: Gunakan saran dari AI jika deteksi lokal gagal
            elif data.category_suggestion:
                category = db.query(Category)\
                    .filter(func.lower(Category.name) == data.category_suggestion.lower())\
                    .first()
                if category:
                    data.category_ids = [category.id]

        transaction = TransactionRepository.create(db, user_id, data)

        # 🔥 LEARNING: simpan kebiasaan user
        if data.category_ids and data.description:
            CategorizationService.learn(
                db,
                user_id,
                data.description,
                data.category_ids[0]
            )
        
        return transaction

    # 📋 GET ALL (with optional filter later)
    @staticmethod
    def get_all(db: Session, user_id):
        return TransactionRepository.get_all(db, user_id)

    # 🔍 GET BY ID
    @staticmethod
    def get_by_id(db: Session, user_id, transaction_id):
        transaction = db.query(Transaction)\
            .filter(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            ).first()

        if not transaction:
            return {"error": "Transaction not found"}

        return transaction

    # ✏️ UPDATE
    @staticmethod
    def update(db: Session, user_id, transaction_id, data):
        transaction = db.query(Transaction)\
            .filter(
                Transaction.id == transaction_id,
                # Transaction.user_id == user_id
            ).first()

        if not transaction:
            return {"error": "Transaction not found"}

        # update fields
        transaction.account_id = data.account_id
        transaction.amount = data.amount
        transaction.type = data.type
        transaction.description = data.description
        transaction.transaction_date = data.transaction_date

        # delete old categories
        db.query(TransactionCategory)\
            .filter(TransactionCategory.transaction_id == transaction_id)\
            .delete()

        # insert new categories
        for cat_id in data.category_ids:
            tc = TransactionCategory(
                id=uuid.uuid4(),
                transaction_id=transaction_id,
                category_id=cat_id
            )
            db.add(tc)

        # 🔥 UPDATE: belajar kategori baru
        if data.category_ids and data.description:
            CategorizationService.learn(
                db,
                user_id,
                data.description,
                data.category_ids[0]
            )

        db.commit()
        return transaction

    # ❌ DELETE
    @staticmethod
    def delete(db: Session, user_id, transaction_id):
        transaction = db.query(Transaction)\
            .filter(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id
            ).first()

        if not transaction:
            return {"error": "Transaction not found"}

        # delete relation first
        db.query(TransactionCategory)\
            .filter(TransactionCategory.transaction_id == transaction_id)\
            .delete()

        db.delete(transaction)
        db.commit()

        return {"message": "Deleted successfully"}

    # 💰 SUMMARY
    @staticmethod
    def get_summary(db: Session, user_id):
        total_expense = db.query(func.sum(Transaction.amount))\
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "expense"
            ).scalar() or 0

        total_income = db.query(func.sum(Transaction.amount))\
            .filter(
                Transaction.user_id == user_id,
                Transaction.type == "income"
            ).scalar() or 0

        return {
            "total_expense": float(total_expense),
            "total_income": float(total_income),
            "balance": float(total_income - total_expense)
        }

    # 📊 BY CATEGORY
    @staticmethod
    def get_by_category(db: Session, user_id):
        result = db.query(
            Category.name,
            func.sum(Transaction.amount)
        ).join(TransactionCategory, Category.id == TransactionCategory.category_id)\
         .join(Transaction, Transaction.id == TransactionCategory.transaction_id)\
         .filter(Transaction.user_id == user_id)\
         .group_by(Category.name)\
         .all()

        return [
            {"category": r[0], "total": float(r[1])}
            for r in result
        ]

    # 📅 DAILY SPENDING
    @staticmethod
    def get_daily(db: Session, user_id, tz_name: str = "UTC"):
        # Konversi UTC ke Timezone User sebelum di-grouping
        # PostgreSQL syntax: transaction_date AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Jakarta'
        local_date = func.cast(
            func.timezone(tz_name, func.timezone('UTC', Transaction.transaction_date)),
            date
        )

        result = db.query(
            local_date,
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense"
        ).group_by(local_date)\
         .order_by(local_date)\
         .all()

        return [
            {"date": str(r[0]), "total": float(r[1])}
            for r in result
        ]


    # 🔥 TOP SPENDING
    @staticmethod
    def get_top_spending(db: Session, user_id):
        result = db.query(
            Transaction.description,
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense"
        ).group_by(Transaction.description)\
         .order_by(func.sum(Transaction.amount).desc())\
         .limit(5)\
         .all()

        return [
            {"description": r[0], "total": float(r[1])}
            for r in result
        ]

    # 🧠 INSIGHT GENERATOR (🔥 VALUE UTAMA)
    @staticmethod
    def generate_insight(db: Session, user_id):
        categories = TransactionService.get_by_category(db, user_id)
        summary = TransactionService.get_summary(db, user_id)

        logger.debug(f"Categories: {categories}")
        logger.debug(f"Summary: {summary}")

        total_expense = summary["total_expense"]

        for item in categories:
            if item["category"] == "Jajan":
                percent = (item["total"] / total_expense) * 100 if total_expense else 0

                if percent > 40:
                    return {"message": f"⚠️ Jajan kamu {percent:.0f}% dari total pengeluaran 😬"}
                elif percent > 25:
                    return {"message": f"Jajan kamu lumayan besar ({percent:.0f}%)"}
        
        return {"message": "Pengeluaran kamu masih cukup terkontrol 👍"}