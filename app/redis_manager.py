# app/redis_manager.py
import redis
import json
import time
import hashlib
from app.config import REDIS_URL

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception as e:
    print(f"Redis not available: {e}")
    redis_client = None
    REDIS_AVAILABLE = False

def get_history(user_id, limit=5):
    if not REDIS_AVAILABLE:
        return []
    key = f"chat:{user_id}"
    raw = redis_client.lrange(key, 0, limit - 1)
    return [json.loads(item) for item in raw]

def save_history(user_id, user_msg, bot_msg):
    if not REDIS_AVAILABLE:
        return
    key = f"chat:{user_id}"
    item = json.dumps({'user': user_msg, 'ai': bot_msg, 'ts': time.time()})
    redis_client.lpush(key, item)
    redis_client.ltrim(key, 0, 9)
    redis_client.expire(key, 1800)

def get_cached_response(query: str):
    if not REDIS_AVAILABLE:
        return None
    cache_key = f"rag:resp:{hashlib.md5(query.encode()).hexdigest()}"
    cached = redis_client.get(cache_key)
    return cached if cached else None

def cache_response(query: str, response: str, ttl: int = 3600):
    if not REDIS_AVAILABLE:
        return
    cache_key = f"rag:resp:{hashlib.md5(query.encode()).hexdigest()}"
    redis_client.setex(cache_key, ttl, response)