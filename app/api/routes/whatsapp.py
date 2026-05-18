from app.services.whatsapp_service import handle_message, handle_image_message
from app.services.whatsapp_service import send_whatsapp_message
from fastapi import APIRouter, BackgroundTasks, Request
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()

router = APIRouter()


# 🔐 VERIFY WEBHOOK
@router.get("/webhook/whatsapp")
def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode") or params.get("hub_mode")
    token = params.get("hub.verify_token") or params.get("hub_verify_token")
    challenge = params.get("hub.challenge") or params.get("hub_challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return int(challenge)

    return {"error": "Verification failed"}


# ─── Background task wrappers ───────────────────────────────────────────────

processed_message_ids = set()
MAX_CACHE_SIZE = 1000

async def _process_text(text: str, phone: str):
    """Dijalankan di background: parse teks via AI lalu kirim balasan."""
    try:
        await send_whatsapp_message(phone, "⏳ Sedang diproses...")
        result = await handle_message(text, phone)
        await send_whatsapp_message(phone, result)
    except Exception as e:
        logger.exception(f"Background task error (text): {e}")
        await send_whatsapp_message(phone, "❌ Terjadi kesalahan saat memproses pesan.")


async def _process_image(media_id: str, phone: str):
    """Dijalankan di background: download + parse foto struk lalu kirim balasan."""
    try:
        await send_whatsapp_message(phone, "⏳ Sedang memproses foto struk Anda...")
        result = await handle_image_message(media_id, phone)
        await send_whatsapp_message(phone, result)
    except Exception as e:
        logger.exception(f"Background task error (image): {e}")
        await send_whatsapp_message(phone, "❌ Terjadi kesalahan saat memproses foto struk.")


# 📩 RECEIVE MESSAGE
@router.post("/webhook/whatsapp")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    try:
        # Meta mengirim 'messages' untuk pesan baru, 'statuses' untuk update status
        value = body["entry"][0]["changes"][0]["value"]

        if "messages" in value:
            message = value["messages"][0]
            message_id = message.get("id")
            phone = message["from"]
            msg_type = message.get("type")

            # 🛑 Deduplikasi menggunakan message_id
            if message_id:
                if message_id in processed_message_ids:
                    logger.info(f"Duplicate WhatsApp message_id ignored: {message_id}")
                    return {"status": "ok"}

                processed_message_ids.add(message_id)
                if len(processed_message_ids) > MAX_CACHE_SIZE:
                    processed_message_ids.pop()

            if msg_type == "text":
                text = message["text"]["body"]
                background_tasks.add_task(_process_text, text, phone)

            elif msg_type == "image":
                media_id = message["image"]["id"]
                background_tasks.add_task(_process_image, media_id, phone)

            else:
                await send_whatsapp_message(
                    phone,
                    "Maaf, saya hanya bisa memproses pesan teks atau foto struk."
                )

    except Exception as e:
        logger.exception(f"Error handling WhatsApp webhook: {e}")

    return {"status": "ok"}