# app/scripts/ingestion.py
import uuid
import re
from pathlib import Path
import sys
import os

# === 1. SET PATH ROOT SEBELUM APA PUN ===
current_file_path = os.path.abspath(__file__)
scripts_dir = os.path.dirname(current_file_path)  # /scripts
root_dir = os.path.dirname(scripts_dir)           # /Pra Production

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)  # <-- insert(0) agar prioritas tinggi

# === 2. BARU LOAD ENV & IMPORT INTERNAL MODULE ===
from dotenv import load_dotenv
load_dotenv()

# Sekarang aman mengimpor app.*
from app.config import settings

# === 3. IMPORT DEPENDENSI EKSTERNAL ===
from llama_index.readers.file import PDFReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from qdrant_client.http import models  # dipindah ke sini agar rapi

# =============== FUNGSI-FUNGSI TETAP SAMA ===============
# (copy-paste semua fungsi Anda di sini tanpa perubahan: extract_text_from_pdf_llamaindex, clean_text, dll.)

def extract_text_from_pdf_llamaindex(pdf_path):
    print("\n[1] Ekstraksi PDF dengan LlamaIndex...")
    loader = PDFReader()
    documents = loader.load_data(file=Path(pdf_path))
    full_text = "\n".join([doc.text for doc in documents])
    page_count = len(documents)
    print(f"Ekstraksi selesai, total {page_count} dokumen (file).")
    return full_text

def extract_text_from_web_async(urls):
    from llama_index.readers.web import TrafilaturaWebReader
    print(f"\n[1.1] Ekstraksi dari {len(urls)} URL (async)...")
    reader = TrafilaturaWebReader()
    documents = reader.load_data(urls=urls)
    full_text = "\n".join([doc.text for doc in documents])
    print("Ekstraksi web selesai.")
    return full_text

def clean_text(raw_text):
    print("\n[2] Cleansing text...")
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    print("Cleansing selesai, panjang teks:", len(cleaned))
    return cleaned

def chunk_text(text, chunk_size=500, overlap=100):
    print("\n[3] Chunking text...")
    chunks, start, text_length = [], 0, len(text)
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    print(f"Chunking selesai, total {len(chunks)} chunks.")
    return chunks

def get_embedder(model_name=settings.RAG.EMBEDDING_MODEL_NAME):
    print("\n[4] Loading embedding model:", model_name)
    return SentenceTransformer(model_name)

def store_to_qdrant(chunks, embeddings, collection_name, batch_size=50):
    print("\n[5] Menyimpan embedding ke Qdrant...")
    client = QdrantClient(
        url=settings.RAG.QDRANT_URL,
        api_key=settings.RAG.QDRANT_API_KEY,
        timeout=30
    )

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=len(embeddings[0]),
            distance=Distance.COSINE
        )
    )
    print(f"Collection '{collection_name}' berhasil dibuat/diganti dengan dimensi: {len(embeddings[0])}")

    total = len(chunks)
    for i in range(0, total, batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={"text": chunk},
            )
            for chunk, embedding in zip(batch_chunks, batch_embeddings)
        ]
        client.upsert(collection_name=collection_name, points=points)
        print(f" Batch {i//batch_size + 1}: simpan {len(points)} chunks")

    print(f"Sukses simpan {total} chunks ke collection '{collection_name}'")
    return client

# ================= MAIN =================
if __name__ == "__main__":
    PDF_FILES = [
        "data/Pedoman-BKD-UIN-Salatiga-2023-31012023.pdf",
        "data/RENSTRA-LPM-UIN-SALATIGA.pdf",
        "data/RENSTRA-UIN-SALATIGA-2022-2024-20012023.pdf"
    ]
    WEB_URLS = ["https://uin-salatiga.ac.id", "https://lpm.uin-salatiga.ac.id"]
    COLLECTION_NAME = "my_pdf_collection"

    print(f"\n================ STARTING RAG INGESTION ({COLLECTION_NAME}) ================")

    combined_text = ""
    for f in PDF_FILES:
        try:
            combined_text += extract_text_from_pdf_llamaindex(f)
        except Exception as e:
            print(f"Gagal baca {f}: {e}")

    # web_text = extract_text_from_web_async(WEB_URLS)
    # combined_text += "\n\n" + web_text

    cleaned_text = clean_text(combined_text)
    chunks = chunk_text(cleaned_text, chunk_size=500, overlap=100)

    try:
        embedder = get_embedder()
        embeddings = embedder.encode(chunks, convert_to_tensor=False)
        client = store_to_qdrant(chunks=chunks, embeddings=embeddings, collection_name=COLLECTION_NAME)
        print("\n=== INGESTION SUKSES SELESAI ===")
    except Exception as e:
        print(f"\n=== INGESTION GAGAL TOTAL ===")
        print(f"Periksa Koneksi Qdrant atau API Key di .env. Detail: {e}")
        exit(1)