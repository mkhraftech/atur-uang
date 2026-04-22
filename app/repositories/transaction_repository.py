from sqlalchemy import text
from app.models.transaction import Transaction
from app.models.transaction_category import TransactionCategory
import uuid

class TransactionRepository:

    @staticmethod
    def create(db, user_id, data):
        transaction = Transaction(
            id=uuid.uuid4(),
            user_id=user_id,
            account_id=data.account_id,
            amount=data.amount,
            type=data.type,
            description=data.description,
            transaction_date=data.transaction_date
        )
        db.add(transaction)
        db.flush()

        for cat_id in data.category_ids:
            tc = TransactionCategory(
                id=uuid.uuid4(),
                transaction_id=transaction.id,
                category_id=cat_id
            )
            db.add(tc)

        db.commit()
        return transaction

    @staticmethod
    def get_all(db, user_id):
        # return db.query(Transaction).filter(Transaction.user_id == user_id).all()
        query = """
            SELECT *
            FROM transactions t
            JOIN transaction_categories tc ON t.id = tc.transaction_id
            JOIN categories c ON tc.category_id = c.id
            ORDER BY t.transaction_date DESC
        """
        result = db.execute(text(query))
        rows = result.mappings().all()
        return rows