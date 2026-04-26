from sqlalchemy.orm import Session
from app.models.user import User
from app.models.account import Account
import uuid

class UserRepository:

    @staticmethod
    def get_by_phone(db: Session, phone_number: str) -> User:
        return db.query(User).filter(User.phone_number == phone_number).first()

    @staticmethod
    def get_by_google_id(db: Session, google_id: str) -> User:
        return db.query(User).filter(User.google_id == google_id).first()

    @staticmethod
    def create_user(db: Session, email: str, google_id: str, name: str, picture: str, phone_number: str = None) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email,
            google_id=google_id,
            name=name,
            picture=picture,
            phone_number=phone_number
        )
        db.add(user)
        db.flush() # Get user.id without committing
        
        # Create default account
        account = Account(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Utama",
            type="General"
        )
        db.add(account)
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_phone(db: Session, user_id: uuid.UUID, phone_number: str):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.phone_number = phone_number
            db.commit()
        return user

    @staticmethod
    def update_timezone(db: Session, user_id: uuid.UUID, timezone: str):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.timezone = timezone
            db.commit()
        return user

    @staticmethod
    def get_default_account(db: Session, user_id: uuid.UUID) -> Account:

        return db.query(Account).filter(Account.user_id == user_id).first()
