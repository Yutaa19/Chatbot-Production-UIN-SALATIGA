# app/app.py
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

# Fail-fast config validation
import app.config  
from app.rag_initializer import get_runtime_components



def create_app():
    app = Flask(__name__) 
    
    @app.route('/')
    def index():
        return render_template('index.html')
    # app/app.py

    @app.route('/widget')
    def widget():
        return render_template('widget.html')
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
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_bp)

    app.logger.info("Application started")
    return app

application = create_app()

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)