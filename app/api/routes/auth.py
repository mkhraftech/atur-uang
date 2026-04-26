from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.utils.dependency import get_db
from app.repositories.user_repository import UserRepository
from authlib.integrations.starlette_client import OAuth
import base64
import json
from app.core.logger import logger
from app.services.whatsapp_service import send_whatsapp_message

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@router.get("/login")
async def login(request: Request, phone: str):
    """
    Step 1: Initiate OAuth2 flow. 
    'phone' is passed as a query param and stored in OAuth2 'state'.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI or f"{settings.BASE_URL}/api/v1/auth/callback"
    
    # Encode phone into state (simple base64 for now)
    state_data = {"phone": phone}
    state = base64.b64encode(json.dumps(state_data).encode()).decode()
    
    return await oauth.google.authorize_redirect(request, redirect_uri, state=state)

@router.get("/callback")
async def callback(request: Request, db: Session = Depends(get_db)):
    """
    Step 2: Google redirects back here with 'code' and 'state'.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=400, detail="Gagal mengambil data user dari Google")

        # Decode state to get phone
        state = request.query_params.get('state')
        phone = None
        if state:
            try:
                state_data = json.loads(base64.b64decode(state).decode())
                phone = state_data.get('phone')
            except Exception as e:
                logger.error(f"Gagal decode state: {e}")

        email = user_info.get('email')
        google_id = user_info.get('sub')
        name = user_info.get('name')
        picture = user_info.get('picture')

        # Check if user exists
        user = UserRepository.get_by_google_id(db, google_id)
        
        if user:
            # If user exists but phone is different, update it
            if phone and user.phone_number != phone:
                UserRepository.update_phone(db, user.id, phone)
        else:
            # Create new user
            user = UserRepository.create_user(
                db, 
                email=email, 
                google_id=google_id, 
                name=name, 
                picture=picture, 
                phone_number=phone
            )

        # Notify user via WhatsApp if phone is available
        if phone:
            send_whatsapp_message(
                phone, 
                f"✅ *Pendaftaran Berhasil!*\n\nHalo {name}, akun Anda telah terhubung dengan Google ({email}). Sekarang Anda bisa mulai mencatat transaksi langsung dari sini. 👍"
            )

        return {"message": "Login berhasil! Anda bisa kembali ke WhatsApp.", "user": email}

    except Exception as e:
        logger.exception(f"Error in auth callback: {e}")
        return {"error": str(e)}
