"""
Chat API endpoints - inti dari chatbot RAG.
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
    try:
        # === 1. Validasi input ===
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body harus berupa JSON.'}), 400

        user_query = data.get('query', '').strip()
        if not validate_query(user_query):
            return jsonify({'error': 'Pertanyaan minimal 3 karakter.'}), 400

        if is_rate_limited(session.get('user_id', str(uuid.uuid4()))):
            return jsonify({'error': 'Terlalu banyak permintaan. Silakan coba lagi nanti.'}), 429

        # === 2. Session & cache ===
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        user_id = session['user_id']

        # Cek cache terlebih dahulu
        cached = get_cached_response(user_query)
        if cached:
            save_history(user_id, user_query, cached)
            return jsonify({'answer': cached})

        # === 3. Riwayat percakapan (aman dari None) ===
        history = get_history(user_id, limit=5) or []
        history_text = "\n".join([
            f"User: {h['user']}\nAI: {h['ai']}" for h in history
        ]) if history else ""

        # === 4. RAG: Cari di Qdrant ===
        retrieved_results = search_qdrant(user_query, top_k=3)

        # === 5. Evaluasi relevansi & keputusan Google Search ===
        rag_context = ""
        enable_google_search = False

        if retrieved_results:
            # Filter berdasarkan threshold relevansi
            relevant_docs = [
                doc for doc in retrieved_results
                if doc.get("score", 0) > settings.RAG.RAG_RELEVANCE_THRESHOLD
            ]
            if relevant_docs:
                rag_context = "\n".join([doc["text"] for doc in relevant_docs])
                logger.info("[RAG] Konteks relevan ditemukan. Google Search dinonaktifkan.")
                enable_google_search = False
            else:
                logger.warning("[RAG] Hasil ditemukan tetapi tidak relevan. Mengaktifkan Google Search.")
                enable_google_search = True
        else:
            logger.warning("[RAG] Tidak ada hasil dari Qdrant. Mengaktifkan Google Search.")
            enable_google_search = True

        # === 6. Bangun prompt ===
        system_prompt, user_prompt = construct_prompt(
            user_query=user_query,
            rag_context=rag_context,
            conversation_history=history_text
        )

        # === 7. Panggil LLM utama ===
        answer = ask_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            rag_context=rag_context,
            enable_google_search=enable_google_search
        )

        # === 8. Simpan cache & riwayat ===
        cache_response(user_query, answer, ttl=3600)  # Cache 1 jam
        save_history(user_id, user_query, answer)

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