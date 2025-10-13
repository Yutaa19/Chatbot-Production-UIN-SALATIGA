# app/redis_manager.py
import redis
import json
import time
import hashlib
import logging
from app.config import settings

logger = logging.getLogger(__name__)
# --- Inisialisasi Global ---
redis_client = None
REDIS_AVAILABLE = False  # ← DIDEKLARASIKAN DI SINI

try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connected")
except Exception as e:
    logger.error(f"Redis unavailable: {e}")
    redis_client = None

def _safe_redis_call(func):
    """Decorator untuk aman panggil Redis."""
    def wrapper(*args, **kwargs):
        if redis_client is None:
            return None if func.__name__ != 'save_history' else None
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis call failed in {func.__name__}: {e}")
            return [] if 'get' in func.__name__ else None
    return wrapper

@_safe_redis_call
def get_history(user_id, limit=5):
    key = f"chat:{user_id}"
    raw = redis_client.lrange(key, 0, limit - 1)
    return [json.loads(item) for item in reversed(raw)]

@_safe_redis_call
def save_history(user_id, user_msg, bot_msg):
    key = f"chat:{user_id}"
    item = json.dumps({'user': user_msg, 'ai': bot_msg, 'ts': time.time()})
    pipe = redis_client.pipeline()
    pipe.lpush(key, item)
    pipe.ltrim(key, 0, 9)
    pipe.expire(key, 1800, nx=True)
    pipe.execute()

def _generate_cache_key(query: str) -> str:
    version = f"{settings.RAG.EMBEDDING_MODEL_NAME}:{settings.RAG.COLLECTION_NAME}"
    combined = f"{query}:{version}"
    return f"rag:resp:{hashlib.sha256(combined.encode()).hexdigest()}"

@_safe_redis_call
def get_cached_response(query: str):
    return redis_client.get(_generate_cache_key(query))

@_safe_redis_call
def cache_response(query: str, response: str, ttl: int = 3600):
    redis_client.setex(_generate_cache_key(query), ttl, response)

__all__ = ['redis_client', 'REDIS_AVAILABLE', 'get_history', 'save_history', 'get_cached_response', 'cache_response']