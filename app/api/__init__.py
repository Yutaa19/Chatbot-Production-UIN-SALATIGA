# app/api/__init__.py
from flask import Blueprint

chat_bp = Blueprint('chat', __name__, url_prefix='/api')
health_bp = Blueprint('health', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')  # tambahkan ini

from . import chat, health, admin  # tambahkan 'admin'