# app/api/chat.py
"""
Chat API endpoints - inti dari chatbot RAG.
"""

import uuid
import logging
from flask import request, jsonify, session
from . import chat_bp
from app.config import settings
from app.redis_manager import (
    get_history, save_history,
    get_cached_response, cache_response,
    REDIS_AVAILABLE, redis_client
)
from app.rag_initializer import get_runtime_components  # ✅ NAMA BENAR
from app.core.main import search_qdrant, construct_prompt, ask_gemini  # ✅ PANGGIL LANGSUNG
from app.utils.validators import validate_query

logger = logging.getLogger(__name__)

def is_rate_limited(user_id: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
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
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Body harus berupa JSON.'}), 400

        user_query = data.get('query', '').strip()
        if not validate_query(user_query):
            return jsonify({'error': 'Pertanyaan minimal 3 karakter.'}), 400

        # Gunakan user_id dari session (pastikan app.secret_key di-set!)
        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        user_id = session['user_id']

        # Rate limiting
        if is_rate_limited(user_id):
            return jsonify({
                'error': 'Terlalu banyak permintaan. Coba lagi dalam 1 menit.'
            }), 429

        # Cek cache
        cached = get_cached_response(user_query)
        if cached:
            save_history(user_id, user_query, cached)
            return jsonify({'answer': cached})

        # Riwayat percakapan
        history = get_history(user_id, limit=5)
        history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history])

        # RAG Pipeline — panggil fungsi langsung
        retrieved = search_qdrant(user_query, top_k=3)
        if not retrieved:
            fallback = "Maaf, saya tidak menemukan informasi terkait. Kunjungi https://uin-salatiga.ac.id."
            cache_response(user_query, fallback, ttl=1800)
            save_history(user_id, user_query, fallback)
            return jsonify({'answer': fallback})

        system_prompt, user_prompt = construct_prompt(user_query, retrieved, history_text)
        answer = ask_gemini(system_prompt, user_prompt)  # ✅ Tidak perlu kirim API key — sudah di settings

        # Simpan
        cache_response(user_query, answer, ttl=3600)
        save_history(user_id, user_query, answer)

        return jsonify({'answer': answer})

    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        return jsonify({'error': str(e)}), 400
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return jsonify({'error': 'Gagal terhubung ke layanan AI. Coba lagi.'}), 502
    except Exception as e:
        logger.error(f"Unexpected error in /ask: {e}", exc_info=True)
        return jsonify({
            'error': 'Terjadi gangguan teknis. Tim sedang memperbaiki.'
        }), 500