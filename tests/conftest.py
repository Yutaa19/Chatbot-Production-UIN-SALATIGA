# tests/conftest.py
import os
import pytest

# Load test environment
@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['REDIS_URL'] = 'redis://localhost:6379/15'  # DB 15 khusus testing
    os.environ['QDRANT_URL'] = 'http://localhost:6333'
    os.environ['GEMINI_API_KEY'] = 'fake_api_key_for_testing'
    os.environ['COLLECTION_NAME'] = 'test_campus_knowledge'
    yield
    # Cleanup bisa ditambahkan di sini jika perlu

