import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "tinyllama")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "conversations.db")
    GEMINI_MODEL = "gemini-2.5-flash"
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
