# app/utils/validators.py
"""
Validation utilities for the chatbot application.
"""

import re

# Daftar frasa yang sering digunakan dalam prompt injection
PROMPT_INJECTION_PATTERNS = [
    r"\b(abaikan|ignore|lupakan|forget|bypass|override|disregard)\b",
    r"(system prompt|instruction|role|you are)",
    r"(password|secret|api[_\s]?key|admin)",
]

def validate_query(query: str) -> bool:
    """
    Validate user query for safety, length, and sanity.
    
    Args:
        query (str): The user's query string
        
    Returns:
        bool: True if query is valid, False otherwise
    """
    # 1. Tipe dan keberadaan
    if not isinstance(query, str):
        return False

    # 2. Normalisasi & strip
    stripped = query.strip()
    if not stripped:
        return False

    # 3. Panjang: minimal 3, maksimal 500 karakter
    if len(stripped) < 3 or len(stripped) > 500:
        return False

    # 4. Deteksi prompt injection dasar (case-insensitive)
    lower_query = stripped.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower_query):
            return False

    # 5. (Opsional) Blokir karakter kontrol
    if any(ord(c) < 32 for c in stripped if c not in '\n\t '):
        return False

    return True