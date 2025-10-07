# tests/test_config.py
import os
from app.config import REDIS_URL

def test_redis_url():
    assert REDIS_URL == 'redis://localhost:6379/15'