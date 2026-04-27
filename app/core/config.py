from pydantic.v1 import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # APP
    APP_NAME: str
    APP_VERSION: str

    # DATABASE
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # SECRET KEY
    SECRET_KEY: str

    # WHATSAPP
    VERIFY_TOKEN: str
    WHATSAPP_TOKEN: str
    PHONE_NUMBER_ID: str

    # AI
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    GROQ_API_KEY: str
    GROQ_MODEL: str

    # GOOGLE OAUTH2
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    # GOOGLE_REDIRECT_URI: str
    BASE_URL: str


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# @lru_cache()
def get_settings() -> Settings:
    return Settings()