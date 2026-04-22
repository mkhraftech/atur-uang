from sqlalchemy import text

class CategoryRepository:

    @staticmethod
    def get_all(db, user_id):
        # return db.query(Transaction).filter(Transaction.user_id == user_id).all()
        query = """
            SELECT *
            FROM categories
        """
        result = db.execute(text(query))
        rows = result.mappings().all()
        return rows