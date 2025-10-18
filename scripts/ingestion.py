# app/scripts/ingestion.py
import uuid
import re
import hashlib
import os
import sys
from pathlib import Path

# === 1. SET PATH ROOT ===
current_file_path = os.path.abspath(__file__)
scripts_dir = os.path.dirname(current_file_path)
root_dir = os.path.dirname(scripts_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# === 2. LOAD ENV & INTERNAL MODULES ===
from dotenv import load_dotenv
load_dotenv()

from app.config import settings

# === 3. EXTERNAL DEPENDENCIES ===
from llama_index.readers.file import PDFReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# NLP untuk smart chunking
import nltk
nltk.download('punkt', quiet=True)

# ================= HELPER FUNCTIONS =================

def extract_text_from_pdf_llamaindex(pdf_path):
    print("\n[1] Ekstraksi PDF dengan LlamaIndex...")
    if not os.path.exists(pdf_path):
        print(f"  File tidak ditemukan: {pdf_path}")
        return ""
    loader = PDFReader()
    documents = loader.load_data(file=Path(pdf_path))
    full_text = "\n".join([doc.text for doc in documents])
    page_count = len(documents)
    print(f"  Ekstraksi selesai, total {page_count} dokumen.")
    return full_text

def extract_text_from_web_async(urls):
    from llama_index.readers.web import TrafilaturaWebReader
    cleaned_urls = [url.strip() for url in urls if url.strip().startswith("http")]
    if not cleaned_urls:
        print("\n[1.1] Tidak ada URL valid untuk diekstrak.")
        return ""
    print(f"\n[1.1] Ekstraksi dari {len(cleaned_urls)} URL (async)...")
    reader = TrafilaturaWebReader()
    try:
        documents = reader.load_data(urls=cleaned_urls)
        full_text = "\n".join([doc.text for doc in documents])
        print("  Ekstraksi web selesai.")
        return full_text
    except Exception as e:
        print(f"  Gagal ekstrak web: {e}")
        return ""

def clean_text(raw_text):
    if not raw_text:
        return ""
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def smart_chunk_semantic(text: str, max_chunk_size: int = 512, overlap: int = 64) -> list:
    """Chunk berbasis batas kalimat (NLP-aware)."""
    if not text.strip():
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        sentences = nltk.sent_tokenize(para)
        for sent in sentences:
            test = (current_chunk + " " + sent).strip()
            if len(test) <= max_chunk_size or not current_chunk:
                current_chunk = test
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk)

    # Tambahkan overlap
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
            else:
                prev_words = chunks[i-1].split()[-overlap//5:]
                new_chunk = " ".join(prev_words + chunk.split())
                overlapped.append(new_chunk)
        chunks = overlapped
    return chunks


def get_chunk_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()

def get_embedder(model_name=settings.RAG.EMBEDDING_MODEL_NAME):
    print(f"\n[4] Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)

def store_to_qdrant(chunks, embeddings, collection_name, batch_size=50):
    print(f"\n[5] Menyimpan embedding ke Qdrant (mode: append)...")
    client = QdrantClient(
        url=settings.RAG.QDRANT_URL,
        api_key=settings.RAG.QDRANT_API_KEY,
        timeout=30
    )

    embedding_size = len(embeddings[0]) if len(embeddings) > 0 else 768
    collections = client.get_collections().collections
    collection_names = [col.name for col in collections]

    if collection_name not in collection_names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE)
        )
        print(f"  Collection '{collection_name}' dibuat.")
    else:
        print(f"  Collection '{collection_name}' sudah ada. Menambahkan data...")

    if not chunks:
        print("  Tidak ada chunk untuk disimpan.")
        return client

    total = len(chunks)
    for i in range(0, total, batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        points = [
            PointStruct(
                id=get_chunk_id(chunk),
                vector=emb.tolist(),
                payload={"text": chunk},
            )
            for chunk, emb in zip(batch_chunks, batch_embeddings)
        ]
        client.upsert(collection_name=collection_name, points=points)
        print(f"  Batch {i//batch_size + 1}: simpan {len(points)} chunks")

    print(f"\n=== INGESTION BERHASIL: {total} chunks ===")
    return client

# ================= MAIN =================
if __name__ == "__main__":
    PDF_FILES = [
        "data/uin_salatiga_struktur_organisasi1.pdf",
    ]


    WEB_URLS = [
    "https://www.uinsalatiga.ac.id/#",
    "https://www.uinsalatiga.ac.id/tentang-uin-salatiga/",
    "https://www.uinsalatiga.ac.id/kehidupan-kampus/",
    "https://www.uinsalatiga.ac.id/visi-dan-misi/",
    ""
    ]

    COLLECTION_NAME = "uin_knowledge_base"

    print(f"\n================ STARTING RAG INGESTION ({COLLECTION_NAME}) ================")

    all_chunks = []

    # === Proses PDF ===
    for f in PDF_FILES:
        try:
            text = extract_text_from_pdf_llamaindex(f)
            if not text.strip():
                continue
            else:
                chunks = smart_chunk_semantic(text, max_chunk_size=512, overlap=64)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  Gagal baca {f}: {e}")

    # === Proses Web ===
    try:
        web_text = extract_text_from_web_async(WEB_URLS)
        if web_text.strip():
            web_chunks = smart_chunk_semantic(web_text, max_chunk_size=512, overlap=64)
            all_chunks.extend(web_chunks)
    except Exception as e:
        print(f"  Gagal ekstrak web: {e}")

    if not all_chunks:
        print("\n=== TIDAK ADA DATA UNTUK DIINGEST ===")
        exit(0)

    print(f"\n[3] Total chunks siap di-encode: {len(all_chunks)}")

    try:
        embedder = get_embedder()
        embeddings = embedder.encode(all_chunks, convert_to_tensor=False)
        client = store_to_qdrant(
            chunks=all_chunks,
            embeddings=embeddings,
            collection_name=COLLECTION_NAME
        )
        print("\n=== INGESTION SELESAI DENGAN AMAN ===")
    except Exception as e:
        print(f"\n=== ERROR SAAT INGESTION ===")
        print(f"Detail: {e}")
        exit(1)