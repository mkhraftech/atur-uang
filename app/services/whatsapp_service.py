import requests
import os
import re

from app.services.transaction_service import TransactionService
from app.services.categorization_service import CategorizationService
from app.services.ai_service import ai_service
from app.services.receipt_service import process_receipt_from_path
from app.services.todo_service import TodoService
from app.core.config import get_settings
from app.core.logger import logger
from app.core.database import SessionLocal

from app.repositories.user_repository import UserRepository
from zoneinfo import ZoneInfo
from datetime import datetime

settings = get_settings()

def get_user_now(user):
    tz_name = getattr(user, 'timezone', 'Asia/Jakarta') or 'Asia/Jakarta'
    try:
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now(ZoneInfo("Asia/Jakarta"))


async def handle_message(text: str, phone: str):
    db = SessionLocal()
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
    if text_lower == "summary":
        return await handle_summary(user_id)

    # 📊 HARI INI
    if text_lower == "hari ini":
        return await handle_today(user, user_now)

    # 📋 LIST TODO
    if text_lower in ("list todo", "todo list", "daftar todo"):
        db = SessionLocal()
        return TodoService.list_todos(db, user_id)

    # 🌍 TIMEZONE
    if text_lower == "timezone":
        from zoneinfo import ZoneInfo
        from datetime import datetime
        now_wib = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%H:%M")
        now_wita = datetime.now(ZoneInfo("Asia/Makassar")).strftime("%H:%M")
        now_wit = datetime.now(ZoneInfo("Asia/Jayapura")).strftime("%H:%M")
        
        return (
            f"🌍 Zona waktu Anda: *{user.timezone or 'Asia/Jakarta'}*\n\n"
            f"Waktu Sekarang:\n"
            f"🇮🇩 WIB: {now_wib}\n"
            f"🇮🇩 WITA: {now_wita}\n"
            f"🇮🇩 WIT: {now_wit}"
        )

    if text_lower.startswith("set timezone"):
        # Ambil semua teks setelah 'set timezone' (menggunakan regex agar lebih fleksibel dengan spasi/titik dua)
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
        db = SessionLocal()
        return TodoService.complete_todo(db, user_id, int(match_done.group(2)))

    # 🗑️ HAPUS <nomor>
    match_del = re.match(r"^(hapus|delete|del)\s+(\d+)$", text_lower)
    if match_del:
        db = SessionLocal()
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



def parse_transaction(text: str):
    # ambil angka
    amount_match = re.search(r'\d+', text)

    if not amount_match:
        return None, None

    amount = int(amount_match.group())
    description = text.replace(str(amount), "").strip()

    return description, amount

from datetime import date
from app.schemas.transaction import TransactionCreate


async def handle_transaction_input(text, user_id, user_now):
    db = SessionLocal()

    # Menggunakan AI untuk parsing teks natural
    ai_data = await ai_service.parse_transaction_text(text, user_now)
    
    amount = ai_data.get("amount")
    description = ai_data.get("description") or text
    category_suggestion = ai_data.get("category_suggestion")
    trx_type = ai_data.get("type", "expense")

    if not amount:
        return "Maaf, saya tidak mengerti nominal transaksinya. Bisa diulang? (Contoh: kopi 15rb)"

    # Cari Account ID default user
    account = UserRepository.get_default_account(db, user_id)
    account_id = account.id if account else "00000000-0000-0000-0000-000000000000"
    
    data = {
        "account_id": account_id,
        "amount": amount,
        "type": trx_type,
        "description": description,
        "transaction_date": user_now,
        "category_ids": []
    }

    # Konversi dict ke Pydantic model agar tidak error 'attribute'
    transaction_data = TransactionCreate(**data)

    trx = TransactionService.create_transaction(db, user_id, transaction_data)

    msg = f"✅ Dicatat:\n📌 *{description}*\n💰 *Rp {amount:,.00f}*"
    if category_suggestion:
        msg += f"\n📁 Kategori: {category_suggestion}"
        
    return msg

async def handle_summary(user_id):
    db = SessionLocal()

    summary = TransactionService.get_summary(db, user_id)

    return (
        f"📊 *Ringkasan Keuangan*:\n\n"
        f"📉 Pengeluaran: Rp {summary['total_expense']:,.00f}\n"
        f"📈 Pemasukan: Rp {summary['total_income']:,.00f}\n"
        f"💳 Saldo: *Rp {summary['balance']:,.00f}*"
    )

def send_whatsapp_message(to, text):
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

    response = requests.post(url, headers=headers, json=payload)
    logger.debug(f"WHATSAPP RESPONSE: {response.status_code} - {response.text}")
    return response.json()

async def download_whatsapp_media(media_id):
    # 1. Get Media URL from Meta
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        logger.error(f"Error fetching media URL: {res.text}")
        return None
        
    media_url = res.json().get("url")
    if not media_url:
        return None

    # 2. Download the binary data
    res_bin = requests.get(media_url, headers=headers)
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
    db = SessionLocal()
    user = UserRepository.get_by_phone(db, phone)
    if not user:
        login_url = f"{settings.BASE_URL}/api/v1/auth/login?phone={phone}"
        return f"Maaf, nomor Anda belum terdaftar. Silakan login di sini: {login_url}"

    user_id = user.id


    # Kirim pesan awal agar user tau bot sedang bekerja
    # (Opsional, tapi bagus untuk UX karena parsing butuh waktu)
    # send_whatsapp_message(phone, "⏳ Sedang memproses foto struk Anda...")

    file_path = await download_whatsapp_media(media_id)
    if not file_path:
        return "Gagal mengunduh foto struk."

    db = SessionLocal()
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
    db = SessionLocal()
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
    db = SessionLocal()
    parsed = await ai_service.parse_todo_reminder(text, user_now)

    todo_text = parsed.get("todo_text") or text
    remind_at_str = parsed.get("remind_at")

    if remind_at_str:
        from datetime import datetime
        try:
            # Parse ISO 8601 dengan timezone
            remind_at = datetime.fromisoformat(remind_at_str)
            return TodoService.add_reminder(db, user_id, phone, todo_text, remind_at)
        except Exception:
            logger.warning(f"Gagal parse remind_at: {remind_at_str}, simpan sebagai todo biasa")

    return TodoService.add_todo(db, user_id, phone, todo_text)