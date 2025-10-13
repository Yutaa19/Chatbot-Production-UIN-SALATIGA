# app/rag_initializer.py
from functools import lru_cache
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

from app.config import settings

@lru_cache(maxsize=1)
def get_runtime_components():
    """
    Inisialisasi Klien RAG runtime (Qdrant, Embedder, LLM) sekali dan cache.
    HANYA menjalankan koneksi, TIDAK menjalankan ingestion data.
    """
    print("[INIT] Mempersiapkan klien RAG (Qdrant & Embedder)...")

    # --- 1. Klien QDRANT ---
    qdrant_client = QdrantClient(
        url=settings.RAG.QDRANT_URL,
        api_key=settings.RAG.QDRANT_API_KEY
    )

    # --- 2. Model Embedding ---
    embedder = SentenceTransformer(settings.RAG.EMBEDDING_MODEL_NAME)

    # --- 3. Klien LLM (Gemini) ---
    genai.configure(api_key=settings.GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')

    return {
        'qdrant_client': qdrant_client,
        'embedder': embedder,
        'gemini_model': gemini_model,
        'collection_name': settings.RAG.COLLECTION_NAME,
    }