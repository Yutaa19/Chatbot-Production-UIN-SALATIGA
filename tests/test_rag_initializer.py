# tests/test_rag_initializer.py
from unittest.mock import patch
from app.rag_initializer import get_rag_components

@patch('app.rag_initializer.store_to_qdrant')
@patch('app.rag_initializer.get_embedder')
@patch('app.rag_initializer.chunk_text')
@patch('app.rag_initializer.clean_text')
@patch('app.rag_initializer.extract_text_from_web_async')
@patch('app.rag_initializer.extract_text_from_pdf_llamaindex')
def test_rag_components_initialization(
    mock_pdf, mock_web, mock_clean, mock_chunk, mock_embedder, mock_store
):
    # Mock return values
    mock_pdf.return_value = "Teks PDF dummy"
    mock_web.return_value = "Teks web dummy"
    mock_clean.return_value = "teks bersih"
    mock_chunk.return_value = ["chunk1", "chunk2"]
    mock_embedder.return_value.encode.return_value = [[0.1, 0.2], [0.3, 0.4]]
    mock_store.return_value = "mock_qdrant_client"

    # Panggil fungsi
    rag = get_rag_components()

    # Pastikan semua komponen ada
    assert 'client' in rag
    assert 'embedder' in rag
    assert 'search_function' in rag
    assert 'llm_function' in rag