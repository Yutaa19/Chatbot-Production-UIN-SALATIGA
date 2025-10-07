# app/api/admin.py
"""
Admin endpoints for monitoring and light maintenance.
Protected by ADMIN_SECRET_KEY from environment.
"""

import os
from flask import request, jsonify
from . import admin_bp
from app.redis_manager import redis_client
import json

def require_admin_auth():
    """Middleware sederhana: cek secret key di header."""
    auth_key = request.headers.get('X-Admin-Secret')
    expected = os.getenv('ADMIN_SECRET_KEY')
    if not expected:
        return jsonify({'error': 'ADMIN_SECRET_KEY tidak dikonfigurasi'}), 500
    if auth_key != expected:
        return jsonify({'error': 'Akses ditolak'}), 403
    return None

@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    """Dapatkan statistik sistem: query, cache, user."""
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        # Hitung jumlah user unik (approximasi via Redis keys)
        chat_keys = redis_client.keys("chat:*")
        user_count = len(chat_keys)

        # Hitung cache hit/miss (jika Anda simpan counter - opsional)
        # Untuk versi dasar, kita hanya tampilkan info Redis
        redis_info = redis_client.info()

        return jsonify({
            'status': 'ok',
            'active_users': user_count,
            'redis_memory_mb': round(redis_info.get('used_memory', 0) / (1024 * 1024), 2),
            'redis_keys': redis_info.get('db0', {}).get('keys', 0),
            'note': 'Statistik riil memerlukan logging tambahan. Ini adalah estimasi dasar.'
        })
    except Exception as e:
        return jsonify({'error': f'Gagal ambil statistik: {str(e)}'}), 500

@admin_bp.route('/cache/reset', methods=['POST'])
def reset_cache():
    """Reset semua cache Redis (kecuali riwayat chat)."""
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        # Hanya hapus key yang terkait cache, bukan riwayat
        cache_keys = redis_client.keys("rag:resp:*")
        for key in cache_keys:
            redis_client.delete(key)
        return jsonify({
            'message': f'Cache berhasil direset. {len(cache_keys)} entri dihapus.'
        })
    except Exception as e:
        return jsonify({'error': f'Gagal reset cache: {str(e)}'}), 500

@admin_bp.route('/history/<user_id>', methods=['GET'])
def get_user_history(user_id):
    """Lihat riwayat percakapan user (untuk debugging)."""
    auth_error = require_admin_auth()
    if auth_error:
        return auth_error

    try:
        key = f"chat:{user_id}"
        raw = redis_client.lrange(key, 0, -1)
        history = [json.loads(item) for item in raw]
        return jsonify({
            'user_id': user_id,
            'history': history
        })
    except Exception as e:
        return jsonify({'error': f'Gagal ambil riwayat: {str(e)}'}), 500