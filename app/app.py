# app/app.py
import os
from flask import Flask, render_template
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    # Get the root directory of the project
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(root_dir, 'templates'),
                static_folder=os.path.join(root_dir, 'static'))
    app.secret_key = os.getenv('FLASK_SECRET_KEY')

    # === SETUP LOGGING ===
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Handler untuk chatbot.log (rotasi 10 MB, simpan 5 file)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'chatbot.log'),
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # === Register API Blueprints ===
    from app.api import chat_bp, health_bp
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)

    # === Frontend Route ===
    @app.route('/')
    def home():
        return render_template('index.html')

    return app

# Entry point for Gunicorn
application = create_app()

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_ENV', 'production') != 'production'
    application.run(debug=debug_mode, host='0.0.0.0', port=5000)