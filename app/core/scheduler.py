from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.database import SessionLocal
from app.repositories.todo_repository import TodoRepository
from app.core.logger import logger

scheduler = AsyncIOScheduler()


async def _check_reminders():
    """Dipanggil tiap menit: cek reminder yang sudah jatuh tempo dan kirim WA."""
    try:
        with SessionLocal() as db:
            due = TodoRepository.get_due_reminders(db)
            if not due:
                return

            # Import di sini untuk hindari circular import
            from app.services.whatsapp_service import send_whatsapp_message

            for todo in due:
                msg = f"⏰ *Reminder!*\n📌 {todo.text}"
                send_whatsapp_message(todo.phone, msg)
                TodoRepository.mark_reminded(db, todo)
                logger.info(f"Reminder sent for todo {todo.id} to {todo.phone}")
    except Exception as e:
        logger.error(f"Error in scheduler reminder check: {e}")


def start_scheduler():
    scheduler.add_job(
        _check_reminders,
        trigger=IntervalTrigger(minutes=1),
        id="reminder_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — checking reminders every minute.")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")
