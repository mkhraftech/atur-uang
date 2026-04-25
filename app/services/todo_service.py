from sqlalchemy.orm import Session
from app.repositories.todo_repository import TodoRepository
from app.core.logger import logger


class TodoService:

    @staticmethod
    def add_todo(db: Session, user_id: str, phone: str, text: str) -> str:
        todo = TodoRepository.create(db, user_id, phone, text)
        logger.info(f"Todo created: {todo.id} for user {user_id}")
        return f"✅ Todo ditambahkan:\n📌 *{text}*"

    @staticmethod
    def add_reminder(db: Session, user_id: str, phone: str, text: str, remind_at) -> str:
        todo = TodoRepository.create(db, user_id, phone, text, remind_at=remind_at)
        # Format waktu lokal (WIB = UTC+7)
        from datetime import timezone, timedelta
        wib = timezone(timedelta(hours=7))
        time_str = remind_at.astimezone(wib).strftime("%d %b %Y %H:%M") if remind_at else "-"
        logger.info(f"Reminder created: {todo.id} at {remind_at}")
        return f"⏰ Reminder diset!\n📌 *{text}*\n🕐 {time_str} WIB"

    @staticmethod
    def list_todos(db: Session, user_id: str) -> str:
        todos = TodoRepository.get_pending(db, user_id)
        if not todos:
            return "📋 Todo list kosong. Ketik *todo: <tugas>* untuk menambahkan."

        lines = ["📋 *Todo List:*\n"]
        for i, t in enumerate(todos, 1):
            icon = "⏰" if t.remind_at else "📌"
            reminder_info = ""
            if t.remind_at:
                from datetime import timezone, timedelta
                wib = timezone(timedelta(hours=7))
                reminder_info = f" _(reminder: {t.remind_at.astimezone(wib).strftime('%d %b %H:%M')} WIB)_"
            lines.append(f"{i}. {icon} {t.text}{reminder_info}")

        lines.append("\nKetik *selesai <nomor>* atau *hapus <nomor>* untuk mengelola.")
        return "\n".join(lines)

    @staticmethod
    def complete_todo(db: Session, user_id: str, index: int) -> str:
        todo = TodoRepository.mark_done(db, user_id, index)
        if not todo:
            return f"❌ Todo nomor {index} tidak ditemukan."
        return f"✅ Todo *{todo.text}* ditandai selesai!"

    @staticmethod
    def delete_todo(db: Session, user_id: str, index: int) -> str:
        success = TodoRepository.delete(db, user_id, index)
        if not success:
            return f"❌ Todo nomor {index} tidak ditemukan."
        return f"🗑️ Todo nomor {index} dihapus."
