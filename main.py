# from fastapi import FastAPI
# from app.routes import webhook_router
# from app.core.config import get_settings
# from app.core.database import SessionLocal, Base, engine
import uvicorn

# app = FastAPI(title=get_settings().APP_NAME)
# app.include_router(webhook_router)

# @app.on_event("startup")
# def startup_event():
#     Base.metadata.create_all(bind=engine)

# @app.get("/")
# def home():
#     return {"message": "Server is running!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
