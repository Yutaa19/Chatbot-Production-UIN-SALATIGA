"""
Chat API endpoints - inti dari chatbot RAG.
(Versi ini sudah di-upgrade untuk Reranking)
"""

import uuid
import logging
from flask import request, jsonify, session
from . import chat_bp
from app.config import settings
from app.redis_manager import (
    get_history,
    save_history,
    get_cached_response,
    cache_response,
    REDIS_AVAILABLE,
    redis_client
)
from app.analytics_manager import log_interaction 
import time
from app.core.main import search_qdrant, construct_prompt, ask_gemini
from app.utils.validators import validate_query

logger = logging.getLogger(__name__)


def is_rate_limited(user_id: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
    """Rate limiting sederhana berbasis Redis."""
    if not REDIS_AVAILABLE:
        return False
    key = f"rate_limit:{user_id}"
    current = redis_client.get(key)
    if current is None:
        redis_client.setex(key, window_seconds, 1)
        return False
    elif int(current) < max_requests:
        redis_client.incr(key)
        return False
    else:
        return True


@chat_bp.route('/ask', methods=['POST'])
def ask():
    # Catat waktu mulai di paling awal
    start_time = time.time()
    
    # Definisikan variabel metadata di awal
    retrieval_source = "UNKNOWN"
    llm_model = "N/A"
    input_tokens = 0
    output_tokens = 0
    latency_ms = 0
    
    try:
        # === 1. Validasi input ===
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body harus berupa JSON.'}), 400

        user_query = data.get('query', '').strip()
        if not validate_query(user_query):
            return jsonify({'error': 'Pertanyaan minimal 3 karakter.'}), 400

        # === 2. Session & Rate Limiting (DIOPTIMALKAN) ===
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        user_id = session['user_id']

        if is_rate_limited(user_id):
            return jsonify({'error': 'Terlalu banyak permintaan. Silakan coba lagi nanti.'}), 429
        
        # === 3. Cek Cache ===
        cached = get_cached_response(user_query)
        if cached:
            logger.info(f"Menyajikan respons dari CACHE untuk query: {user_query}")
            
            latency_ms = int((time.time() - start_time) * 1000)
            retrieval_source = "CACHE"
            
            save_history(user_id, user_query, cached)
            
            try:
                log_interaction(
                    session_id=user_id,
                    query=user_query,
                    response=cached,
                    source=retrieval_source,
                    model=llm_model,  # "N/A"
                    in_tokens=input_tokens,   # 0
                    out_tokens=output_tokens, # 0
                    latency=latency_ms
                )
            except Exception as e:
                logger.error(f"Gagal mencatat log (CACHE) ke DB: {e}", exc_info=True)
                
            return jsonify({'answer': cached})

        # === 4. Riwayat percakapan (aman dari None) ===
        history = get_history(user_id, limit=5) or []
        history_text = "\n".join([
            f"User: {h['user']}\nAI: {h['ai']}" for h in history
        ]) if history else ""

        # === 5. RAG: Cari di Qdrant (Versi Reranking) ===
        # Fungsi search_qdrant kini mengembalikan 'text', 'payload', dan 'rerank_score'
        retrieved_results = search_qdrant(user_query, top_k=3) #

        # === 6. Evaluasi relevansi & keputusan Google Search ===
        # <<< REVISI RERANKER >>>
        # Logika filter diubah total untuk menggunakan 'rerank_score'
        # ==========================================================
        rag_context = ""
        enable_google_search = False

        if retrieved_results:
            # Filter berdasarkan 'rerank_score' baru yang "pintar"
            relevant_docs = [
                doc for doc in retrieved_results
                if doc.get("rerank_score", -99) > settings.RAG.RERANKER_THRESHOLD
            ]
            
            if relevant_docs:
                # Kita hanya ambil 'text' untuk konteks
                rag_context = "\n".join([doc["text"] for doc in relevant_docs])
                logger.info(f"[RAG] Konteks relevan ditemukan ({len(relevant_docs)} doc). Google Search dinonaktifkan.")
                enable_google_search = False
                retrieval_source = "RAG_INTERNAL"
            else:
                # Ini terjadi jika Reranker memberi skor rendah pada SEMUA kandidat
                logger.warning("[RAG] Hasil ditemukan tetapi Reranker menilai tidak relevan. Mengaktifkan Google Search.")
                enable_google_search = True
                retrieval_source = "RAG_GOOGLE"
        else:
            # Ini terjadi jika Qdrant tidak menemukan apa-apa
            logger.warning("[RAG] Tidak ada hasil dari Qdrant (Retrieve). Mengaktifkan Google Search.")
            enable_google_search = True
            retrieval_source = "RAG_GOOGLE"
        
        # ==========================================================
        # <<< AKHIR REVISI RERANKER >>>
        # ==========================================================

        # === 7. Bangun prompt ===
        system_prompt, user_prompt = construct_prompt(
            user_query=user_query,
            rag_context=rag_context,
            conversation_history=history_text
        )

        # === 8. Panggil LLM utama ===
        llm_result = ask_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            rag_context=rag_context,
            enable_google_search=enable_google_search
        )

        answer = llm_result.get('answer', 'Maaf, terjadi kesalahan saat memproses jawaban.')
        metadata = llm_result.get('metadata', {})
        
        retrieval_source = metadata.get('source', retrieval_source) 
        llm_model = metadata.get('model', 'gemini-unknown')
        input_tokens = metadata.get('input_tokens', 0)
        output_tokens = metadata.get('output_tokens', 0)

        # === 9. Hitung Latensi Final ===
        latency_ms = int((time.time() - start_time) * 1000)

        # === 10. Simpan cache, riwayat, dan LOG ANALITIK ===
        cache_response(user_query, answer, ttl=3600)  # Cache 1 jam
        save_history(user_id, user_query, answer)

        try:
            log_interaction(
                session_id=user_id,
                query=user_query,
                response=answer,
                source=retrieval_source,
                model=llm_model,
                in_tokens=input_tokens,
                out_tokens=output_tokens,
                latency=latency_ms
            )
        except Exception as e:
            logger.error(f"Gagal mencatat log (LLM) ke DB: {e}", exc_info=True)

        return jsonify({'answer': answer})

    except ValueError as e:
        logger.warning(f"Input tidak valid: {e}")
        return jsonify({'error': str(e)}), 400

    except ConnectionError as e:
        logger.error(f"Kesalahan koneksi ke LLM: {e}")
        return jsonify({
            'error': 'Sistem sedang mengalami gangguan sementara. Mohon coba lagi dalam beberapa saat.'
        }), 503

    except Exception as e:
        logger.error(f"Error tak terduga di /ask: {e}", exc_info=True)
        return jsonify({
            'error': 'Terjadi gangguan teknis. Tim sedang memperbaiki.'
        }), 500