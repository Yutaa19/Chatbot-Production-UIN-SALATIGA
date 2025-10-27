import re
import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from flask import current_app, g
import requests
from bs4 import BeautifulSoup

# --- Google Generative AI SDK (Resmi & Terbaru) ---

from google.genai import types
import google.generativeai as genai 

# --- Konfigurasi & Komponen Internal ---
from app.config import settings
from app.rag_initializer import get_runtime_components

logger = logging.getLogger(__name__)


# ===================================================================
# 1. PREPROCESSING QUERY (Bahasa Indonesia)
# ===================================================================
# Fungsi preprocessing query
def preprocess_query(query):
    """
    Preprocessing query untuk meningkatkan hasil pencarian
    """
    # 1. Convert ke lowercase
    processed = query.lower()
    
    # 2. Hapus karakter khusus tapi pertahankan yang penting
    processed = re.sub(r'[^\w\s\u00C0-\u017F]', ' ', processed)
    
    # 3. Normalisasi whitespace
    processed = re.sub(r'\s+', ' ', processed).strip()
    
    # 4. Untuk bahasa Indonesia, bisa tambah stemming sederhana
    # Misalnya: "pendaftaran" -> "daftar", "penerimaan" -> "terima"
    indonesian_stem = {
        'pendaftaran': 'daftar',
        'penerimaan': 'terima',
        'pengumuman': 'umum',
        'mahasiswa': 'mhs',
        'kampus': 'kampus',
        'universitas': 'univ',
        'fakultas': 'fak',
        'jurusan': 'jur',
        'program': 'prodi',
        'studi': 'prodi'
    }
    
    words = processed.split()
    processed_words = []
    for word in words:
        if word in indonesian_stem:
            processed_words.append(indonesian_stem[word])
        else:
            processed_words.append(word)
    
    return ' '.join(processed_words)


# ===================================================================
# 2. GOOGLE SEARCH TOOL (Untuk Tool Use)
# ===================================================================
def _google_search_tool(query: str) -> str:
    """
    Tool eksternal: Google Search.
    Ganti dengan integrasi nyata di production (misal: Google Programmable Search Engine).
    """
    logger.info(f"[TOOL] Google Search dipanggil untuk: '{query}'")

    # Menggunakan logger Flask dengan request_id
    current_app.logger.info(
        f"[TOOL_STUB] Google Search dipanggil untuk: '{query}'",
        extra={'request_id': g.get('request_id'), 'query': query}
    )
    
    # STUB DEVELOPMENT — GANTI DI PRODUCTION
    return (
        f"Di lingkungan production, sistem akan mencari informasi terkini tentang '{query}' "
        f"melalui Google Search dan memberikan jawaban berbasis hasil tersebut."
    )


# ===================================================================
# 3. RAG: PENCARIAN DI QDRANT
# ===================================================================
def search_qdrant(query: str, top_k: int = 3):
    """
    Cari dokumen relevan di Qdrant dengan preprocessing, embedding, dan validasi vektor.
    Mengembalikan: List[{'text': str, 'score': float}]
    """
    request_id = g.get('request_id') # Ambil request_id untuk logging
    
    current_app.logger.info(
        f"[RAG] Mencari dokumen untuk query: '{query}'",
        extra={'request_id': request_id, 'query': query}
    )

    try:
        rag = get_runtime_components()
        client = rag["qdrant_client"]
        embedder = rag["embedder"]
        collection_name = rag["collection_name"]
    except Exception as e:
        logger.error(f"[RAG] Gagal memuat komponen RAG: {e}")
        return []

    try:
        # Preprocess & encode
        processed_query = preprocess_query(query)
        query_vec = embedder.encode(
            [processed_query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )[0]

        # Ambil kandidat dari Qdrant
        hits = client.search(
            collection_name=collection_name,
            query_vector=query_vec.tolist(),
            limit=top_k * 2,  # Ambil lebih banyak untuk fleksibilitas
            with_payload=True,
            with_vectors=True
        )

        if not hits:
            return []

        # Filter dokumen valid
        texts, vectors = [], []
        for hit in hits:
            text = hit.payload.get("text", "").strip()
            vector = hit.vector
            if not text or vector is None:
                continue
            if np.any(np.isnan(vector)):
                logger.warning("Melewati dokumen dengan vektor NaN")
                continue
            texts.append(text)
            vectors.append(vector)

        if not vectors:
            return []

        # Hitung cosine similarity
        vectors = np.array(vectors)
        sims = cosine_similarity([query_vec], vectors)[0]

        # Bangun hasil
        results = [
            {"text": text, "score": float(sim)}
            for text, sim in zip(texts, sims)
        ]
        results.sort(key=lambda x: x["score"], reverse=True)

        # Ambil top_k terbaik
        final_results = results[:top_k]
        logger.info(f"[RAG] Skor relevansi: {[round(r['score'], 3) for r in final_results]}")
        return final_results

    except Exception as e:
        logger.error(f"[RAG] Error saat pencarian: {e}", exc_info=True)
        return []


# ===================================================================
# 4. KONSTRUKSI PROMPT
# ===================================================================
def construct_prompt(user_query: str, rag_context: str = "", conversation_history: str = "") -> tuple[str, str]:
    """
    Bangun system prompt dan user prompt untuk LLM.
    """
    system_prompt = (
    "Anda adalah Chatbot UIN_SAGA resmi Kampus UIN Salatiga. "
    "Jawab dengan profesional, ramah, sopan, dan akurat. "
    "1. **Prioritaskan** selalu informasi dari KONTEKS INTERNAL jika tersedia dan relevan. "
    "2. Gunakan Google Search **hanya jika** KONTEKS INTERNAL tidak ada ATAU pertanyaan bersifat sangat baru (berita, acara mendatang, info pimpinan terbaru) yang tidak mungkin ada di konteks internal. "
    "3. Jangan mengarang, jangan menyebut proses teknis (seperti 'berdasarkan pencarian Google' atau 'dari konteks RAG'), dan batasi jawaban maksimal 2-3 kalimat ringkas."
    "jangan pernah menyatakan bahwa anda adalah model AI ataupun LLM. anda hanya bisa menyatakan CHATBOT UIN-SAGA. "
    )

    parts = []
    if conversation_history.strip():
        parts.append(f"RIWAYAT PERCAKAPAN:\n{conversation_history}")
    if rag_context.strip():
        parts.append(f"KONTEKS INTERNAL:\n{rag_context}")
    else:
        parts.append("KONTEKS INTERNAL: Tidak tersedia.")
    parts.append(f"PERTANYAAN USER:\n{user_query}")

    user_prompt = "\n\n".join(parts)
    return system_prompt, user_prompt


# ===================================================================
# 5. FUNGSI UTAMA: ORKESTRATOR LLM (RAG + GOOGLE SEARCH)
# ===================================================================

# Pastikan Anda mengimpor 'requests' dan 'os' di bagian atas file
import requests
import os

GOOGLE_SEARCH_API_KEY = settings.GOOGLE_SEARCH_API_KEY
SEARCH_ENGINE_ID = settings.SEARCH_ENGINE_ID

# ... (impor lain dan definisi GOOGLE_SEARCH_API_KEY, SEARCH_ENGINE_ID) ...

def extract_main_content(url: str) -> str:
    """Mengekstrak teks utama dari URL menggunakan BeautifulSoup (versi sederhana)."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'} # Beberapa web butuh user-agent
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Heuristik sederhana: ambil teks dari tag <p>, <article>, atau <body>
        paragraphs = soup.find_all('p')
        if not paragraphs:
             # Fallback ke body jika tidak ada <p>
            body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
            return body_text[:1500] # Batasi panjangnya

        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        return content[:1500] # Batasi panjang konten yang diekstrak
    except Exception as e:
        current_app.logger.warning(
            f"[TOOL] Gagal ekstrak konten dari {url}: {e}",
            extra={'request_id': g.get('request_id')}
        )
        return ""

def search_google(query: str) -> dict:
    """Melakukan Google Search DAN ekstraksi konten dari hasil teratas."""
    request_id = g.get('request_id')

    if not GOOGLE_SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        current_app.logger.error(
            "[TOOL] Google Search API Key/Engine ID tidak diatur.",
            extra={'request_id': request_id}
        )
        return {"error": "Layanan pencarian tidak terkonfigurasi."}

    url = "https://www.googleapis.com/customsearch/v1"
    # Ambil 5 hasil untuk cadangan jika ekstraksi gagal
    params = {'key': GOOGLE_SEARCH_API_KEY, 'cx': SEARCH_ENGINE_ID, 'q': query, 'num': 5}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        results = response.json()

        extracted_results = []
        if 'items' in results:
            # Coba ekstrak konten dari 2-3 hasil teratas
            count = 0
            for item in results.get('items', []):
                link = item.get('link')
                snippet = item.get('snippet', '')
                title = item.get('title', 'Tanpa Judul')

                if link and count < 3: # Batasi ekstraksi ke 3 URL teratas
                    content = extract_main_content(link)
                    if content:
                         extracted_results.append({
                            "extracted_content": content, # <-- Konten halaman web
                            "snippet": snippet,
                            "source_title": title,
                            "url": link
                        })
                         count += 1
                    else:
                        # Jika ekstraksi gagal, pakai snippet saja
                        extracted_results.append({
                            "extracted_content": snippet, # Fallback ke snippet
                            "snippet": snippet,
                            "source_title": title,
                            "url": link
                        })
                elif snippet: # Untuk hasil ke-4 dst, cukup pakai snippet
                     extracted_results.append({
                            "extracted_content": snippet,
                            "snippet": snippet,
                            "source_title": title,
                            "url": link
                        })

        if not extracted_results:
            return {"status": "not_found", "message": "Tidak ada hasil pencarian yang relevan."}

        # Kembalikan hasil yang sudah diekstrak
        return {"status": "success", "results": extracted_results}

    except requests.exceptions.RequestException as e:
        current_app.logger.error(
            f"[TOOL] Error Google Search API: {e}",
            extra={'request_id': request_id, 'query': query}, exc_info=True
        )
        return {"error": f"Error layanan pencarian: {e}"}
# ... (Kode di atas tetap sama) ...

# Asumsi: settings, logger, dan fungsi search_google sudah didefinisikan di atas
def ask_gemini(
    system_prompt: str,
    user_prompt: str,
    rag_context: str = "",
    enable_google_search: bool = False,
) -> str:
    """
    Menggunakan 'generate_content' (stateless) dengan riwayat (history)
    yang HANYA berisi format 'dict' murni untuk menghindari error serialisasi.
    """
    request_id = g.get('request_id')
    
    current_app.logger.info(
        f"[LLM] Memanggil {settings.GEMINI_MODEL_NAME}. Custom Search: {enable_google_search}",
        extra={'request_id': request_id}
    )
    # --- 1. Tools & Model Initialization (Sudah Benar) ---
    tools = [search_google] if enable_google_search else []
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL_NAME,
        system_instruction=system_prompt,
        tools=tools,
        safety_settings={
             types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: types.HarmBlockThreshold.BLOCK_NONE,
             types.HarmCategory.HARM_CATEGORY_HARASSMENT: types.HarmBlockThreshold.BLOCK_NONE,
             types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: types.HarmBlockThreshold.BLOCK_NONE,
             types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: types.HarmBlockThreshold.BLOCK_NONE,
        }
    )
    generation_config = genai.GenerationConfig(
        temperature=0.2,
        max_output_tokens=2048,
    )

    # --- 2. Bangun Riwayat (Format dict) ---
    prompt_to_send = []
    if rag_context.strip() and rag_context != "Data internal tidak memuat informasi spesifik ini.":
        prompt_to_send.append(f"KONTEKS RAG:\n---\n{rag_context}\n---")
    prompt_to_send.append(f"PERTANYAAN USER:\n{user_prompt}")
    
    # 'history' adalah list yang HANYA berisi dict
    history = [
        {'role': 'user', 'parts': [{"text": "\n\n".join(prompt_to_send)}]}
    ]

    try:
        # --- 3. Panggil Model (Stateless) ---
        response = model.generate_content(
            history, # Kirim list [dict]
            generation_config=generation_config
        )

        # --- 4. Loop Eksekusi Function Calling (Stateless) ---
        while response.candidates[0].content.parts[0].function_call:
            fc = response.candidates[0].content.parts[0].function_call
            
            # --- PERBAIKAN KRITIS 1: Konversi 'Content' object (permintaan model) ke 'dict' ---
            model_request_dict = {
                'role': 'model',
                'parts': [
                    # Ubah objek 'Part' menjadi 'dict'
                    {'function_call': {'name': fc.name, 'args': dict(fc.args)}}
                ]
            }
            history.append(model_request_dict)
            # -------------------------------------------------------------------------

            if fc.name == "search_google":
                logger.info(f"[TOOL] Model meminta Google Search dengan query: {dict(fc.args)}")
                
                result_dict = search_google(**dict(fc.args)) # Ini dict, sudah benar
                
                # --- PERBAIKAN KRITIS 2: Konversi 'FunctionResponse' (jawaban kita) ke 'dict' ---
                history.append({
                    'role': 'function',
                    'parts': [
                        # Ubah objek 'types.FunctionResponse' menjadi 'dict'
                        {'function_response': {'name': 'search_google', 'response': result_dict}}
                    ]
                })
                # --------------------------------------------------------------------------

                # Panggil model LAGI dengan riwayat [dict, dict, dict]
                response = model.generate_content(
                    history,
                    generation_config=generation_config
                )
            else:
                # ... (Handle fungsi tidak dikenal) ...
                logger.error(f"Model meminta fungsi yang tidak dikenal: {fc.name}")
                history.append({
                    'role': 'function',
                    'parts': [
                        {'function_response': {'name': fc.name, 'response': {"error": "Fungsi tidak tersedia."}}}
                    ]
                })
                response = model.generate_content(history, generation_config=generation_config)

        # --- 5. Ambil Jawaban Final ---
        answer = response.text.strip()
        
        if not answer:
            return "Maaf, saya tidak dapat memberikan jawaban saat ini."
            
        return answer

    except Exception as e:
        logger.error(f"[LLM] Error kritis: {e}", exc_info=True)
        raise ConnectionError(f"Gagal memproses permintaan: {str(e)}")