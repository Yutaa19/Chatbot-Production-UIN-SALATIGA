# tests/test_redis_manager.py
import redis
from app.redis_manager import (
    get_history, save_history,
    get_cached_response, cache_response,
    redis_client
)

def test_redis_connection():
    assert redis_client.ping() is True

def test_save_and_get_history():
    user_id = "test_user_123"
    save_history(user_id, "Halo", "Hai juga!")
    history = get_history(user_id, limit=1)
    assert len(history) == 1
    assert history[0]['user'] == "Halo"
    assert history[0]['ai'] == "Hai juga!"

def test_cache_response_and_retrieve():
    query = "Apa visi UIN?"
    answer = "Menjadi universitas unggul berbasis Wasathiyyah."
    cache_response(query, answer, ttl=10)
    cached = get_cached_response(query)
    assert cached == answer