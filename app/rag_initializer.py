# app/rag_initializer.py
"""
Singleton-style RAG initializer with lazy loading.
Ensures RAG components are loaded only once and reused across requests.
"""

import os
from functools import lru_cache

# Import core RAG functions from your existing modules
from app.core.main import (
    extract_text_from_pdf_llamaindex,
    extract_text_from_web_async,
    clean_text,
    chunk_text,
    store_to_qdrant,
    ask_gemini,
    get_embedder,
    search_qdrant,
    construct_prompt
)


@lru_cache(maxsize=1)
def get_rag_components():
    """
    Initialize RAG system once and cache it.
    Called only on first /ask request -> saves memory on startup.
    """
    print("[INIT] Initializing RAG components (one-time)...")

    # === Load & process knowledge base ===
    # Use existing PDF files from data folder
    pdf_files = [
        "data/Pedoman-BKD-UIN-Salatiga-2023-31012023.pdf",
        "data/RENSTRA-LPM-UIN-SALATIGA.pdf",
        "data/RENSTRA-UIN-SALATIGA-2022-2024-20012023.pdf"
    ]
    
    # Extract text from multiple PDFs
    pdf_text = ""
    for pdf_file in pdf_files:
        try:
            text = extract_text_from_pdf_llamaindex(pdf_file)
            pdf_text += f"\n\n=== {pdf_file} ===\n\n" + text
        except Exception as e:
            print(f"Error reading {pdf_file}: {e}")
            continue
    
    # Clean URLs (remove trailing spaces!)
    urls_list = [
        "https://www.uinsalatiga.ac.id/",
        "https://www.uinsalatiga.ac.id/tentang-uin-salatiga/",
        "https://www.uinsalatiga.ac.id/kehidupan-kampus/",
        "https://www.uinsalatiga.ac.id/visi-dan-misi/",
        "https://www.uinsalatiga.ac.id/logo/",
        "https://www.uinsalatiga.ac.id/bendera/",
        "https://www.uinsalatiga.ac.id/mars-dan-hymne/",
        "https://www.uinsalatiga.ac.id/akreditasi/",
        "https://www.uinsalatiga.ac.id/akreditasi-program-studi/",
        "https://www.uinsalatiga.ac.id/pimpinan/",
    ]
    urls_list = [url.strip() for url in urls_list if url.strip()]

    web_text = extract_text_from_web_async(urls_list)

    # Combine texts
    combined_text = pdf_text
    if web_text.strip():
        combined_text += "\n\n=== TEKS DARI WEB UIN SALATIGA ===\n\n" + web_text

    cleaned_text = clean_text(combined_text)
    chunks = chunk_text(cleaned_text, chunk_size=500, overlap=100)

    # Embed & store
    embedder = get_embedder()
    embeddings = embedder.encode(chunks, convert_to_tensor=False)

    client = store_to_qdrant(
        chunks=chunks,
        embeddings=embeddings,
        qdrant_url=os.getenv('QDRANT_URL', 'http://localhost:6333'),
        api_key=os.getenv('QDRANT_API_KEY', ''),
        collection_name=os.getenv('COLLECTION_NAME', 'campus_knowledge')
    )

    return {
        'client': client,
        'embedder': embedder,
        'collection_name': os.getenv('COLLECTION_NAME', 'campus_knowledge'),
        'search_function': search_qdrant,
        'prompt_function': construct_prompt,
        'llm_function': ask_gemini,
        'gemini_api_key': os.getenv('GEMINI_API_KEY'),
        'gemini_model': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    }