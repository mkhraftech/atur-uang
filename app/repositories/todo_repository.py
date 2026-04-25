from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.todo import Todo
import uuid


class TodoRepository:

    @staticmethod
    def create(db: Session, user_id: str, phone: str, text: str, remind_at=None) -> Todo:
        todo = Todo(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            phone=phone,
            text=text,
            remind_at=remind_at,
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def get_pending(db: Session, user_id: str) -> list[Todo]:
        """Ambil semua todo yang belum selesai."""
        return (
            db.query(Todo)
            .filter(Todo.user_id == uuid.UUID(user_id), Todo.is_done == False)
            .order_by(Todo.created_at)
            .all()
        )

    @staticmethod
    def mark_done(db: Session, user_id: str, index: int) -> Todo | None:
        """Tandai todo ke-N (1-indexed) sebagai selesai."""
        todos = TodoRepository.get_pending(db, user_id)
        if index < 1 or index > len(todos):
            return None
        todo = todos[index - 1]
        todo.is_done = True
        db.commit()
        return todo

    @staticmethod
    def delete(db: Session, user_id: str, index: int) -> bool:
        """Hapus todo ke-N (1-indexed)."""
        todos = TodoRepository.get_pending(db, user_id)
        if index < 1 or index > len(todos):
            return False
        db.delete(todos[index - 1])
        db.commit()
        return True

    @staticmethod
    def get_due_reminders(db: Session) -> list[Todo]:
        """Ambil semua reminder yang sudah jatuh tempo dan belum dikirimi notif."""
        now = datetime.now(timezone.utc)
        return (
            db.query(Todo)
            .filter(
                Todo.remind_at != None,
                Todo.remind_at <= now,
                Todo.is_done == False,
                Todo.is_reminded == False,
            )
            .all()
        )

    @staticmethod
    def mark_reminded(db: Session, todo: Todo):
        todo.is_reminded = True
        todo.is_done = True
        db.commit()
