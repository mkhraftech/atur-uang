import logging
from app.core.logger import logger
from app.core.config import get_settings
from fastapi import FastAPI
from app.api.routes.whatsapp import router as whatsapp_router
from app.api.routes.auth import router as auth_router
from app.core.database import Base, engine
from app import models  # noqa: F401 — register all tables
from app.core.scheduler import start_scheduler, stop_scheduler
from starlette.middleware.sessions import SessionMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# Diperlukan oleh Authlib untuk menyimpan state OAuth2
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


@app.on_event("startup")
def startup_event():
    try:
        logger.info("Starting database connection...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database connected")
    except Exception as e:
        logger.error(e)
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

app.include_router(whatsapp_router)
app.include_router(auth_router)
