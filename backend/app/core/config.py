from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Knowledge Inbox"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"]
    )

    # Storage Paths
    DATA_DIR: str = "/tmp/data" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else "./data"
    DB_PATH: str = "/tmp/data/knowledge_inbox.db" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else "./data/knowledge_inbox.db"
    CHROMA_PERSIST_DIR: str = "/tmp/data/chroma" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else "./data/chroma"

    # AI Providers Configuration
    LLM_PROVIDER: str = "auto"          # "openai", "gemini", "groq", "local", "auto"
    EMBEDDING_PROVIDER: str = "auto"    # "openai", "gemini", "local", "auto"

    # OpenAI Keys & Models
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Gemini Keys & Models
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "models/gemini-3.6-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Groq Keys & Models
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # RAG & Chunking Parameters
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_THRESHOLD: float = 0.15

    # Scraping limits & Security
    SCRAPER_TIMEOUT_SECONDS: float = 12.0
    MAX_SCRAPE_CONTENT_LENGTH: int = 120000
    USER_AGENT: str = "AIKnowledgeInbox/1.0 (Content Intelligence Bot)"

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env", os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.env"), os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure data directories exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
