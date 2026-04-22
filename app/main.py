from app.core.config import get_settings
from fastapi import FastAPI
from app.api.routes.transaction import router as transaction_router
from app.api.routes.insight import router as insight_router
from app.api.routes.summary import router as summary_router
from app.api.routes.category import router as category_router
from app.api.routes.whatsapp import router as whatsapp_router
from app.api.routes.receipt import router as receipt_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

app.include_router(transaction_router)
app.include_router(insight_router)
app.include_router(summary_router)
app.include_router(category_router)
app.include_router(whatsapp_router)
app.include_router(receipt_router)