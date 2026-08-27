import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./chroma_db")
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "./documents")

    # App Control
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
    
    # User lists
    ADMIN_USER_IDS: list[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip().isdigit()
    ]
    ALLOWED_USER_IDS: list[int] = [
        int(x.strip()) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip().isdigit()
    ]

    # RAG & Memory
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "3"))
    MEMORY_ENABLED: bool = os.getenv("MEMORY_ENABLED", "true").lower() in ("true", "1", "yes")
    SCHEDULER_ENABLED: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("true", "1", "yes")
    MAX_DOCUMENT_SIZE_MB: int = int(os.getenv("MAX_DOCUMENT_SIZE_MB", "10"))

    def __init__(self):
        # Create necessary directories
        os.makedirs(self.STORAGE_PATH, exist_ok=True)
        # Ensure the directory for the SQLite database exists if a path is provided
        db_path = self.DATABASE_URL.replace("sqlite:///", "")
        if db_path:
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

settings = Settings()
