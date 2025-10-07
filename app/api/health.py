# app/api/health.py
"""
Health check endpoints for monitoring and readiness probes.
"""

from flask import jsonify
from . import health_bp
import redis
from app.config import REDIS_URL
from qdrant_client import QdrantClient
import os

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Liveness & readiness probe - cek koneksi ke dependensi kritis."""
    checks = {
        'flask': True,
        'redis': False,
        'qdrant': False
    }

    # Cek Redis
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        checks['redis'] = True
    except Exception as e:
        checks['redis_error'] = str(e)

    # Cek Qdrant
    try:
        client = QdrantClient(
            url=os.getenv('QDRANT_URL', 'http://localhost:6333'),
            api_key=os.getenv('QDRANT_API_KEY', None)
        )
        client.get_collections()
        checks['qdrant'] = True
    except Exception as e:
        checks['qdrant_error'] = str(e)

    status = 200 if all(checks[key] for key in ['flask', 'redis', 'qdrant']) else 503
    return jsonify(checks), status