from app.services.whatsapp_service import handle_message, handle_image_message
from app.services.whatsapp_service import send_whatsapp_message
from fastapi import APIRouter, Request
import requests
import os
from app.core.config import get_settings

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


# 📩 RECEIVE MESSAGE
@router.post("/webhook/whatsapp")
async def receive_message(request: Request):
    body = await request.json()

    try:
        # Meta mengirim 'messages' untuk pesan baru, dan 'statuses' untuk update status (sent, delivered, read)
        value = body["entry"][0]["changes"][0]["value"]
        
        if "messages" in value:
            message = value["messages"][0]
            phone = message["from"]
            msg_type = message.get("type")

            if msg_type == "text":
                text = message["text"]["body"]
                response_text = await handle_message(text, phone)
            elif msg_type == "image":
                media_id = message["image"]["id"]
                response_text = await handle_image_message(media_id, phone)
            else:
                response_text = "Maaf, saya hanya bisa memproses pesan teks atau foto struk."

            send_whatsapp_message(phone, response_text)

    except Exception as e:
        print("Error:", e)

    return {"status": "ok"}