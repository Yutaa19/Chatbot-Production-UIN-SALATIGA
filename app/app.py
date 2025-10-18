# app/app.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

# Fail-fast config validation
from app.config import settings
from app.rag_initializer import get_runtime_components



def create_app():
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(__name__, 
                # Tentukan lokasi folder templates secara eksplisit
                template_folder=os.path.join(ROOT_DIR, 'templates'), 
                static_folder=os.path.join(ROOT_DIR, 'static'))

    app.secret_key = settings.FLASK_SECRET_KEY

    @app.route('/')
    def widget():
        return render_template('wigdet.html')
    if not app.debug and not app.testing:
        os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler('logs/chatbot.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    # --- RAG Initialization (Graceful Degradation) ---
    app.rag_clients = None
    try:
        app.rag_clients = get_runtime_components()
        app.logger.info("RAG system online")
    except Exception as e:
        app.logger.warning(f"RAG system offline: {e}")

    # --- Blueprints ---
    from app.api import chat_bp, health_bp, admin_bp
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)  # tetap di /health
    app.register_blueprint(admin_bp)   # tetap di /admin

    app.logger.info("Application started")
    return app

application = create_app()

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)