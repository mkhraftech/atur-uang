import httpx
import os
import re
import uuid
from datetime import datetime, date
from zoneinfo import ZoneInfo

from app.services.transaction_service import TransactionService
from app.services.categorization_service import CategorizationService
from app.services.ai_service import ai_service
from app.services.receipt_service import process_receipt_from_path
from app.services.todo_service import TodoService
from app.core.config import get_settings
from app.core.logger import logger
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.transaction import TransactionCreate

settings = get_settings()

def get_user_now(user):
    tz_name = getattr(user, 'timezone', 'Asia/Jakarta') or 'Asia/Jakarta'
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now(ZoneInfo("Asia/Jakarta"))


async def handle_message(text: str, phone: str):
    try:
        with SessionLocal() as db:
            user = UserRepository.get_by_phone(db, phone)

            if not user:
                login_url = f"{settings.BASE_URL}/api/v1/auth/login?phone={phone}"
                return (
                    f"👋 *Selamat datang di Atur Uang!*\n\n"
                    f"Sepertinya nomor Anda belum terdaftar. Untuk mulai menggunakan asisten keuangan ini, "
                    f"silakan hubungkan akun Google Anda melalui link di bawah ini:\n\n"
                    f"🔗 {login_url}\n\n"
                    f"Setelah berhasil, Anda bisa langsung mencatat pengeluaran di sini! 😊"
                )

            user_id = user.id
            text_lower = text.lower().strip()
            user_now = get_user_now(user)

            # 📊 SUMMARY
            if text_lower in ("summary", "bulan ini", "bulan lalu"):
                return await handle_monthly_summary(user, user_now, text_lower)

            # 📊 HARI INI
            if text_lower == "hari ini":
                return await handle_today(user, user_now)

            # 📋 LIST TODO
            if text_lower in ("list todo", "todo list", "daftar todo"):
                return TodoService.list_todos(db, user_id)

            # 🌍 TIMEZONE
            if text_lower == "timezone":
                now_wib = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%H:%M")
                now_wita = datetime.now(ZoneInfo("Asia/Makassar")).strftime("%H:%M")
                now_wit = datetime.now(ZoneInfo("Asia/Jayapura")).strftime("%H:%M")
                
                return (
                    f"🌍 Zona waktu Anda: *{user.timezone or 'Asia/Jakarta'}*\n\n"
                    f"Waktu Sekarang:\n"
                    f"WIB: {now_wib}\n"
                    f"WITA: {now_wita}\n"
                    f"WIT: {now_wit}"
                )

            if text_lower.startswith("set timezone"):
                match = re.search(r"set\s+timezone[:\s]+(.+)", text, re.IGNORECASE)
                if match:
                    new_tz = match.group(1).strip()
                    try:
                        ZoneInfo(new_tz) # Validate
                        UserRepository.update_timezone(db, user_id, new_tz)
                        return f"✅ Zona waktu berhasil diubah ke: *{new_tz}*"
                    except Exception as e:
                        logger.error(f"Gagal set timezone '{new_tz}': {e}")
                        return f"❌ Zona waktu tidak valid: *{new_tz}*\n\nContoh yang benar: `Asia/Jakarta`, `Asia/Makassar`, `Asia/Jayapura`."
                else:
                    return "❌ Format salah. Gunakan: `set timezone <nama_zona>`"

            # ✅ SELESAI <nomor>
            match_done = re.match(r"^(selesai|done)\s+(\d+)$", text_lower)
            if match_done:
                return TodoService.complete_todo(db, user_id, int(match_done.group(2)))

            # 🗑️ HAPUS <nomor>
            match_del = re.match(r"^(hapus|delete|del)\s+(\d+)$", text_lower)
            if match_del:
                return TodoService.delete_todo(db, user_id, int(match_del.group(2)))

            # ➕ TODO / REMINDER (natural language)
            is_todo = text_lower.startswith("todo:") or text_lower.startswith("todo ")
            is_reminder = any(text_lower.startswith(kw) for kw in (
                "ingatkan", "remind", "reminder", "pengingat"
            ))
            if is_todo or is_reminder:
                return await handle_todo_reminder(text, user_id, phone, user_now)

            # ➕ INPUT TRANSACTION
            return await handle_transaction_input(text, user_id, user_now)
    except Exception as e:
        logger.exception(f"Error handling message: {e}")
        return "⚠️ Maaf, terjadi kesalahan saat memproses pesan Anda. Silakan coba lagi nanti."



def parse_transaction(text: str):
    # ambil angka
    amount_match = re.search(r'\d+', text)

    if not amount_match:
        return None, None

    amount = int(amount_match.group())
    description = text.replace(str(amount), "").strip()

    return description, amount




async def handle_transaction_input(text, user_id, user_now):
    with SessionLocal() as db:
        # Menggunakan AI untuk parsing teks natural
        ai_data = await ai_service.parse_transaction_text(text, user_now)
        
        # Get list of transactions (support both list structure and single dict fallback)
        transactions_list = []
        if isinstance(ai_data, dict):
            if "transactions" in ai_data and isinstance(ai_data["transactions"], list):
                transactions_list = ai_data["transactions"]
            elif ai_data.get("amount"):
                transactions_list = [ai_data]
        elif isinstance(ai_data, list):
            transactions_list = ai_data

        if not transactions_list:
            return "Maaf, saya tidak mengerti nominal transaksinya. Bisa diulang? (Contoh: kopi 15rb)"

        # Cari Account ID default user
        account = UserRepository.get_default_account(db, user_id)
        account_id = account.id if account else "00000000-0000-0000-0000-000000000000"
        
        recorded_messages = []
        for item in transactions_list:
            amount = item.get("amount")
            if not amount:
                continue
            
            description = item.get("description") or text
            category_suggestion = item.get("category_suggestion")
            trx_type = item.get("type", "expense")

            # Check if there's a custom date/time parsed by the AI
            item_date = user_now
            if item.get("date"):
                parsed_dt = None
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                    try:
                        parsed_dt = datetime.strptime(item.get("date").strip(), fmt)
                        break
                    except ValueError:
                        continue
                if parsed_dt:
                    item_date = parsed_dt.replace(tzinfo=user_now.tzinfo)
            
            data = {
                "account_id": account_id,
                "amount": amount,
                "type": trx_type,
                "description": description,
                "transaction_date": item_date,
                "category_ids": []
            }

            # Konversi dict ke Pydantic model agar tidak error 'attribute'
            transaction_data = TransactionCreate(**data)
            TransactionService.create_transaction(db, user_id, transaction_data)

            msg = f"📌 *{description}*\n💰 *Rp {amount:,.00f}*"
            if category_suggestion:
                msg += f"\n📁 Kategori: {category_suggestion}"
            recorded_messages.append(msg)

        if not recorded_messages:
            return "Maaf, saya tidak mengerti nominal transaksinya. Bisa diulang? (Contoh: kopi 15rb)"

        if len(recorded_messages) == 1:
            return f"✅ Dicatat:\n{recorded_messages[0]}"
        else:
            joined_list = "\n\n".join(recorded_messages)
            return f"✅ Berhasil mencatat {len(recorded_messages)} transaksi:\n\n{joined_list}"

async def handle_monthly_summary(user, user_now, command):
    import calendar
    import datetime as dt
    user_id = user.id
    tz_name = user.timezone or "Asia/Jakarta"
    
    month_ids = {
        "January": "Januari", "February": "Februari", "March": "Maret", "April": "April",
        "May": "Mei", "June": "Juni", "July": "Juli", "August": "Agustus",
        "September": "September", "October": "Oktober", "November": "November", "December": "Desember"
    }

    def format_month_id(year, month):
        temp_date = dt.date(year, month, 1)
        eng_name = temp_date.strftime("%B")
        ind_name = month_ids.get(eng_name, eng_name)
        return f"{ind_name} {year}"

    with SessionLocal() as db:
        if command == "summary":
            # All-time summary
            summary = TransactionService.get_summary(db, user_id)
            title = "📊 *Ringkasan Keuangan (Semua Waktu)*"
        else:
            if command == "bulan ini":
                start_date = dt.date(user_now.year, user_now.month, 1)
                _, last_day = calendar.monthrange(user_now.year, user_now.month)
                end_date = dt.date(user_now.year, user_now.month, last_day)
                month_label = format_month_id(user_now.year, user_now.month)
                title = f"📊 *Ringkasan Keuangan Bulan Ini ({month_label})*"
            else: # "bulan lalu"
                if user_now.month == 1:
                    last_month_year = user_now.year - 1
                    last_month = 12
                else:
                    last_month_year = user_now.year
                    last_month = user_now.month - 1
                
                start_date = dt.date(last_month_year, last_month, 1)
                _, last_day = calendar.monthrange(last_month_year, last_month)
                end_date = dt.date(last_month_year, last_month, last_day)
                month_label = format_month_id(last_month_year, last_month)
                title = f"📊 *Ringkasan Keuangan Bulan Lalu ({month_label})*"

            summary = TransactionService.get_monthly_summary(db, user_id, start_date, end_date, tz_name)

        return (
            f"{title}:\n\n"
            f"📉 Pengeluaran: Rp {summary['total_expense']:,.00f}\n"
            f"📈 Pemasukan: Rp {summary['total_income']:,.00f}\n"
            f"💳 Saldo: *Rp {summary['balance']:,.00f}*"
        )

async def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{settings.PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.debug(f"WHATSAPP RESPONSE: {response.status_code} - {response.text}")
        return response.json()

async def download_whatsapp_media(media_id):
    # 1. Get Media URL from Meta
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code != 200:
            logger.error(f"Error fetching media URL: {res.text}")
            return None
            
        media_url = res.json().get("url")
        if not media_url:
            return None

        # 2. Download the binary data
        res_bin = await client.get(media_url, headers=headers)
        if res_bin.status_code != 200:
            logger.error(f"Error downloading media: {res_bin.text}")
            return None

    # 3. Save to uploads/
    os.makedirs("uploads", exist_ok=True)
    import time
    file_path = f"uploads/whatsapp_{int(time.time())}.jpg"
    
    with open(file_path, "wb") as f:
        f.write(res_bin.content)
        
    return file_path

async def handle_image_message(media_id, phone):
    with SessionLocal() as db:
        user = UserRepository.get_by_phone(db, phone)
        if not user:
            login_url = f"{settings.BASE_URL}/api/v1/auth/login?phone={phone}"
            return f"Maaf, nomor Anda belum terdaftar. Silakan login di sini: {login_url}"

        user_id = user.id

        file_path = await download_whatsapp_media(media_id)
        if not file_path:
            return "Gagal mengunduh foto struk."

        result = await process_receipt_from_path(db, file_path, user_id)

        if result.get("success"):
            data = result["data"]
            return (
                f"✅ *Struk Berhasil Dicatat!*\n\n"
                f"📌 Merchant: {data['merchant']}\n"
                f"💰 Total: *Rp {data['amount']:,.00f}*\n"
                f"📅 Tanggal: {data['date']}\n"
                f"📝 Deskripsi: {data['description']}"
            )
        else:
            return f"❌ Gagal memproses struk: {result.get('error')}"

async def handle_today(user, user_now):
    with SessionLocal() as db:
        today_str = user_now.strftime("%Y-%m-%d")
        tz_name = user.timezone or "Asia/Jakarta"

        daily = TransactionService.get_daily(db, user.id, tz_name)

        # Cari data yang tanggalnya cocok dengan hari ini di local timezone user
        today_data = next((d for d in daily if d["date"] == today_str), None)

        if not today_data:
            return "Belum ada transaksi hari ini"

        return f"📅 Hari ini ({user_now.strftime('%d %b')}): *Rp {today_data['total']:,.00f}*"


async def handle_todo_reminder(text: str, user_id: str, phone: str, user_now: datetime) -> str:
    """Parse teks todo/reminder dengan AI, simpan ke DB."""
    with SessionLocal() as db:
        parsed = await ai_service.parse_todo_reminder(text, user_now)

        todo_text = parsed.get("todo_text") or text
        remind_at_str = parsed.get("remind_at")

        if remind_at_str:
            try:
                # Parse ISO 8601 dengan timezone
                remind_at = datetime.fromisoformat(remind_at_str)
                return TodoService.add_reminder(db, user_id, phone, todo_text, remind_at)
            except Exception:
                logger.warning(f"Gagal parse remind_at: {remind_at_str}, simpan sebagai todo biasa")

        return TodoService.add_todo(db, user_id, phone, todo_text)
