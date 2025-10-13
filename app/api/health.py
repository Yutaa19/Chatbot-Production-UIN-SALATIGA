# app/api/health.py
"""
Health check endpoints for monitoring and readiness probes.
"""

from flask import jsonify
from . import health_bp
from app.config import settings
from app.redis_manager import redis_client, REDIS_AVAILABLE
from app.rag_initializer import get_runtime_components

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Liveness & readiness probe using actual application clients."""
    checks = {
        'app': 'ok',
        'redis': 'unknown',
        'qdrant': 'unknown'
    }

    # --- Cek Redis (gunakan klien yang sama dengan aplikasi) ---
    if REDIS_AVAILABLE and redis_client is not None:
        try:
            redis_client.ping()
            checks['redis'] = 'ok'
        except Exception as e:
            checks['redis'] = 'down'
            checks['redis_error'] = str(e)
    else:
        checks['redis'] = 'disabled'

    # --- Cek Qdrant (gunakan klien dari rag_initializer) ---
    try:
        rag = get_runtime_components()
        qdrant_client = rag['qdrant_client']
        qdrant_client.get_collections()  # ringan, tidak berat
        checks['qdrant'] = 'ok'
    except Exception as e:
        checks['qdrant'] = 'down'
        checks['qdrant_error'] = str(e)

    # --- Status HTTP ---
    # Redis opsional, jadi hanya Qdrant + App yang wajib
    healthy = (checks['qdrant'] == 'ok')
    status_code = 200 if healthy else 503

    return jsonify(checks), status_code