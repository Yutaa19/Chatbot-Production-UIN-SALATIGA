# app/config.py
import sys
from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError
from dotenv import load_dotenv

load_dotenv()  # Cukup sekali di sini

class RAGSettings(BaseSettings):
    EMBEDDING_MODEL_NAME: str = Field(default="firqaaa/indo-sentence-bert-base")
    QDRANT_URL: str
    QDRANT_API_KEY: str
    TOP_K_RETRIEVAL: int = Field(default=3)
    COLLECTION_NAME: str = Field(default="uin_knowledge_base") 
    RERANKER_MODEL_NAME: str = Field(default="cross-encoder/ms-marco-minilm-l-6-v2") # <<< BARU
    RERANKER_THRESHOLD: float = 0.3 # <<< BARU (Skor reranker beda, 0.1 sdh bagus)
    SPACY_MODEL_NAME: str = Field(default="id_core_news_md")
    EMBEDDING_MODEL_PATH: str = "/app/models_cache"
class AppConfig(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL_NAME: str = Field(default="gemini-2.0-flash-lite")
    GOOGLE_SEARCH_API_KEY: str
    SEARCH_ENGINE_ID: str
    REDIS_URL: str
    DATABASE_URL: str
    FLASK_SECRET_KEY: str = Field(min_length=16)
    ADMIN_SECRET_KEY: str = Field(min_length=16)
    RAG: RAGSettings = Field(default_factory=RAGSettings) 

    class Config:
        extra = "ignore"
        case_sensitive = False

try:
    settings = AppConfig()
    print("Configuration loaded and validated successfully.")
except ValidationError as e:
    print("\n[ERROR] FATAL CONFIG ERROR: Missing or Invalid Environment Variables!")
    missing = [err['loc'][-1] for err in e.errors() if err['type'] == 'missing']
    if missing:
        print("\nPastikan variabel berikut ada di file `.env`:")
        for m in missing:
            print(f"  - {m}")
    sys.exit(1)