# app/api/chat.py
"""
Chat API endpoints - inti dari chatbot RAG.
"""

import uuid
from flask import request, jsonify, session
from . import chat_bp
from app.redis_manager import (
    get_history, save_history,
    get_cached_response, cache_response,
    redis_client
)
from app.rag_initializer import get_rag_components
from app.utils.validators import validate_query

# === RATE LIMITING ===
def is_rate_limited(user_id: str, max_requests: int = 5, window_seconds: int = 60) -> bool:
    from app.redis_manager import REDIS_AVAILABLE
    if not REDIS_AVAILABLE:
        return False  # No rate limiting if Redis is not available
    
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
        print("DEBUG: Starting /api/ask request")
        data = request.get_json()
        print(f"DEBUG: Request data: {data}")
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        user_query = data.get('query', '').strip()
        if not validate_query(user_query):
            return jsonify({'error': 'Pertanyaan minimal 3 karakter.'}), 400

        if 'user_id' not in session:
            session['user_id'] = str(uuid.uuid4())
        user_id = session['user_id']

        # Rate limiting
        if is_rate_limited(user_id, max_requests=5, window_seconds=60):
            return jsonify({
                'error': 'Terlalu banyak permintaan. Coba lagi dalam 1 menit.'
            }), 429

        # Cache check
        cached = get_cached_response(user_query)
        if cached:
            save_history(user_id, user_query, cached)
            return jsonify({'answer': cached})

        # Get conversation history
        history = get_history(user_id, limit=5)
        history_text = "\n".join([f"User: {h['user']}\nAI: {h['ai']}" for h in history])

        # RAG pipeline
        rag = get_rag_components()
        retrieved = rag['search_function'](
            query=user_query,
            client=rag['client'],
            collection_name=rag['collection_name'],
            embedder=rag['embedder'],
            top_k=3
        )

        system_prompt, user_prompt = rag['prompt_function'](
            query=user_query,
            retrieved_chunks=retrieved,
            conversation_history=history_text
        )

        answer = rag['llm_function'](
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            api_key=rag.get('gemini_api_key') or None,
            model_name=rag.get('gemini_model', 'gemini-2.5-flash')
        )

        # Save to cache & history
        cache_response(user_query, answer, ttl=3600)
        save_history(user_id, user_query, answer)

        return jsonify({'answer': answer})

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except ConnectionError:
        return jsonify({'error': 'Gagal terhubung ke layanan AI. Coba lagi.'}), 502
    except Exception as e:
        print(f"DEBUG: Exception in /api/ask: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Terjadi gangguan teknis. Tim sedang memperbaiki.'
        }), 500