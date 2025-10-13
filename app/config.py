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
    COLLECTION_NAME: str = Field(default="my_pdf_collection")  # BENAR: di dalam RAGSettings

class AppConfig(BaseSettings):
    GEMINI_API_KEY: str
    REDIS_URL: str
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