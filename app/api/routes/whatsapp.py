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

async def _process_text(text: str, phone: str):
    """Dijalankan di background: parse teks via AI lalu kirim balasan."""
    try:
        result = await handle_message(text, phone)
        send_whatsapp_message(phone, result)
    except Exception as e:
        logger.exception(f"Background task error (text): {e}")
        send_whatsapp_message(phone, "❌ Terjadi kesalahan saat memproses pesan.")


async def _process_image(media_id: str, phone: str):
    """Dijalankan di background: download + parse foto struk lalu kirim balasan."""
    try:
        result = await handle_image_message(media_id, phone)
        send_whatsapp_message(phone, result)
    except Exception as e:
        logger.exception(f"Background task error (image): {e}")
        send_whatsapp_message(phone, "❌ Terjadi kesalahan saat memproses foto struk.")


# 📩 RECEIVE MESSAGE
@router.post("/webhook/whatsapp")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    try:
        # Meta mengirim 'messages' untuk pesan baru, 'statuses' untuk update status
        value = body["entry"][0]["changes"][0]["value"]

        if "messages" in value:
            message = value["messages"][0]
            phone = message["from"]
            msg_type = message.get("type")

            if msg_type == "text":
                text = message["text"]["body"]
                # Balas segera agar WhatsApp tidak timeout, proses di background
                send_whatsapp_message(phone, "⏳ Sedang diproses...")
                background_tasks.add_task(_process_text, text, phone)

            elif msg_type == "image":
                media_id = message["image"]["id"]
                send_whatsapp_message(phone, "⏳ Sedang memproses foto struk Anda...")
                background_tasks.add_task(_process_image, media_id, phone)

            else:
                send_whatsapp_message(
                    phone,
                    "Maaf, saya hanya bisa memproses pesan teks atau foto struk."
                )

    except Exception as e:
        logger.exception(f"Error handling WhatsApp webhook: {e}")

    return {"status": "ok"}