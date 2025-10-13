# app/__init__.py
"""
Package initializer for UIN Salatiga RAG Chatbot.
Enables modular imports and sets up basic logging.
"""

import logging
import os

# Setup root logger
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
