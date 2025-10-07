# tests/test_main.py
from app.core.main import (
    clean_text,
    chunk_text,
    preprocess_query,
    validate_query  # jika ada di utils, pindah ke sana
)

def test_clean_text():
    raw = "**Visi UIN** adalah kejayaan.\n\n   Banyak   spasi   "
    cleaned = clean_text(raw)
    assert cleaned == "Visi UIN adalah kejayaan. Banyak spasi"

def test_chunk_text():
    text = "a " * 600  # 600 kata
    chunks = chunk_text(text, chunk_size=200, overlap=50)
    assert len(chunks) >= 3
    assert len(chunks[0].split()) <= 200

def test_preprocess_query():
    query = "Apa itu **UIN Salatiga**?"
    processed = preprocess_query(query)
    assert processed == "apa itu uin salatiga"