#!/usr/bin/env python3
# scripts/init_qdrant.py
"""
Inisialisasi knowledge base ke Qdrant.
Jalankan SEKALI saat deploy pertama atau saat ada update konten besar.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.main import (
    extract_text_from_pdf_llamaindex,
    extract_text_from_web_async,
    clean_text,
    chunk_text,
    get_embedder,
    store_to_qdrant
)

def main():
    print("🔄 Memulai inisialisasi knowledge base...")

    # Load env
    from dotenv import load_dotenv
    load_dotenv()

    # Data
    PDF_FILE = "data/sejarah_uin.pdf"
    urls_list = [
        "https://www.uinsalatiga.ac.id/",
        "https://www.uinsalatiga.ac.id/tentang-uin-salatiga/",
        "https://www.uinsalatiga.ac.id/visi-dan-misi/",
        "https://www.uinsalatiga.ac.id/logo/",
        "https://www.uinsalatiga.ac.id/bendera/",
        "https://www.uinsalatiga.ac.id/mars-dan-hymne/",
        "https://www.uinsalatiga.ac.id/akreditasi/",
        "https://www.uinsalatiga.ac.id/pimpinan/"
    ]

    # Ekstraksi
    pdf_text = extract_text_from_pdf_llamaindex(PDF_FILE)
    web_text = extract_text_from_web_async(urls_list)
    combined = pdf_text + ("\n\n=== WEB ===\n\n" + web_text if web_text.strip() else "")
    cleaned = clean_text(combined)
    chunks = chunk_text(cleaned, chunk_size=500, overlap=100)

    # Embed & simpan
    embedder = get_embedder()
    embeddings = embedder.encode(chunks, convert_to_tensor=False)
    client = store_to_qdrant(
        chunks=chunks,
        embeddings=embeddings,
        qdrant_url=os.getenv('QDRANT_URL'),
        qdrant_api_key=os.getenv('QDRANT_API_KEY'),
        collection_name=os.getenv('COLLECTION_NAME', 'campus_knowledge')
    )

    print(f"✅ Berhasil menyimpan {len(chunks)} chunks ke Qdrant!")

if __name__ == "__main__":
    main()