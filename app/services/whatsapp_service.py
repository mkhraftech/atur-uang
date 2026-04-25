import requests
import os

from app.services.transaction_service import TransactionService
from app.services.categorization_service import CategorizationService
from app.services.ai_service import ai_service
from app.services.receipt_service import process_receipt_from_path
from app.core.config import get_settings
from app.core.logger import logger

USER_MAP = {
    "6281938902460": "550e8400-e29b-41d4-a716-446655440000",
    "6287798705864": "550e8400-e29b-41d4-a716-446655440000"
}

settings = get_settings()


async def handle_message(text: str, phone: str):
    user_id = USER_MAP.get(phone)

    if not user_id:
        return "User belum terdaftar"

    text_lower = text.lower()

    # 📊 SUMMARY
    if text_lower == "summary":
        return await handle_summary(user_id)

    # 📊 HARI INI
    if text_lower == "hari ini":
        return await handle_today(user_id)

    # ➕ INPUT TRANSACTION
    return await handle_transaction_input(text, user_id)

import re


def parse_transaction(text: str):
    # ambil angka
    amount_match = re.search(r'\d+', text)

    if not amount_match:
        return None, None

    amount = int(amount_match.group())
    description = text.replace(str(amount), "").strip()

    return description, amount

from datetime import date
from app.core.database import SessionLocal
from app.schemas.transaction import TransactionCreate


async def handle_transaction_input(text, user_id):
    db = SessionLocal()

    # Menggunakan AI untuk parsing teks natural
    ai_data = await ai_service.parse_transaction_text(text)
    
    amount = ai_data.get("amount")
    description = ai_data.get("description") or text
    category_suggestion = ai_data.get("category_suggestion")

    if not amount:
        return "Maaf, saya tidak mengerti nominal transaksinya. Bisa diulang? (Contoh: kopi 15rb)"

    # Cari Category ID berdasarkan saran AI (Opsional)
    # Anda bisa menambahkan logika pencarian Category model di sini jika perlu
    
    data = {
        "account_id": "660e8400-e29b-41d4-a716-446655440001",
        "amount": amount,
        "type": "expense",
        "description": description,
        "transaction_date": date.today(),
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
    user_id = USER_MAP.get(phone)
    if not user_id:
        return "User belum terdaftar"

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

async def handle_today(user_id):
    db = SessionLocal()

    daily = TransactionService.get_daily(db, user_id)

    if not daily:
        return "Belum ada transaksi hari ini"

    today = daily[-1]

    return f"📅 Hari ini: {today['total']}"