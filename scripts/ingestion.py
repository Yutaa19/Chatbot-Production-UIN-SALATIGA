# app/scripts/ingestion.py
# REVISI FINAL - Arsitektur Hibrida (Teks, PDF, Tabel)
# DENGAN NLP PREPROCESSING & CONTEXT-AWARE CHUNKING
# VERSI 2.0: MENGGUNAKAN SEMANTIC CHUNKER (SOLUSI B)

import uuid
import re
import hashlib
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# === 1. SET PATH ROOT ===
current_file_path = os.path.abspath(__file__)
scripts_dir = os.path.dirname(current_file_path)
root_dir = os.path.dirname(scripts_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# === 2. KONFIGURASI ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

try:
    from app.config import settings
except ImportError:
    logger.error("Gagal mengimpor 'app.config'. Pastikan PYTHONPATH sudah benar.")
    sys.exit(1)

# === 3. DEPENDENSI EKSTERNAL ===
import pandas as pd
from bs4 import BeautifulSoup
import requests
import numpy as np

# [DIUBAH] Kita ganti dependensi ke stack LlamaIndex murni
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding # <-- [FIX] Path yang benar
from llama_index.core import Document                     # <-- [BARU] Dibutuhkan oleh SemanticChunker
from llama_index.readers.file import PDFReader# <-- [BARU] Pengganti SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

# ===================================================================
# FUNGSI NLP PREPROCESSING (Pembersih Teks)
# ===================================================================
def preprocess_text_with_nlp(text: str) -> str:
    """
    Membersihkan teks mentah dari PDF menggunakan regex.
    (Fungsi ini tidak berubah, sudah bagus)
    """
    if not text:
        return ""
    # 1. Ganti baris baru yang diikuti huruf kecil dengan spasi
    text = re.sub(r'\n(?=[a-z])', ' ', text)
    # 2. Hapus spasi berlebih atau tab
    text = re.sub(r'[ \t]+', ' ', text)
    # 3. Hapus baris baru yang berlebihan (lebih dari 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 4. Hapus spasi di awal/akhir baris
    text = "\n".join([line.strip() for line in text.split('\n')])
    # 5. Hapus kata-kata yang terlalu pendek (noise)
    text = " ".join([word for word in text.split() if len(word) > 1])
    return text.strip()

# ===================================================================
# LANGKAH 1: EKSTRAKSI KONTEN (Extractor Hibrida)
# ===================================================================
#
# Fungsi extract_pdf, extract_web_tables, dan extract_web_article
# ANDA TIDAK BERUBAH. Semuanya sudah bagus dan
# menghasilkan format List[Dict] yang kita inginkan.
#
def extract_pdf(file_path: str) -> List[Dict[str, Any]]:
    logger.info(f"[EXTRACT-PDF] Memproses: {file_path}")
    if not os.path.exists(file_path):
        logger.warning(f"   File PDF tidak ditemukan: {file_path}")
        return []
    loader = PDFReader()
    documents = loader.load_data(file=Path(file_path))
    metadata = {
        "source_file": os.path.basename(file_path),
        "content_type": "pdf_document"
    }
    processed_nodes = []
    for doc in documents:
        cleaned_text = preprocess_text_with_nlp(doc.text)
        processed_nodes.append({"text": cleaned_text, "metadata": metadata})
    return processed_nodes

def extract_web_tables(url: str) -> List[Dict[str, Any]]:
    logger.info(f"[EXTRACT-TABLE] Mencari tabel di: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        tables_df_list = pd.read_html(requests.get(url, headers=headers).text)
    except ValueError as e:
        logger.warning(f"   Tidak ada tabel ditemukan di {url}. (Error: {e})")
        return []
    except Exception as e:
        logger.error(f"   Gagal mengambil URL {url}. (Error: {e})")
        return []
    nodes = []
    for i, df in enumerate(tables_df_list):
        if df.empty or len(df.columns) < 2:
            continue
        logger.info(f"   Memproses Tabel #{i+1} (Ukuran: {df.shape})")
        for _, row in df.iterrows():
            row_text_parts = []
            for col_name in df.columns:
                cell_value = row[col_name]
                if pd.notna(cell_value):
                    row_text_parts.append(f"{col_name}: {cell_value}")
            contextual_chunk = ". ".join(row_text_parts)
            if contextual_chunk:
                metadata = {
                    "source_url": url,
                    "content_type": "web_table_row",
                    "table_index": i
                }
                nodes.append({"text": contextual_chunk, "metadata": metadata})
    logger.info(f"   Total {len(nodes)} baris tabel (node) diekstrak dari {url}")
    return nodes

def extract_web_article(url: str) -> List[Dict[str, Any]]:
    logger.info(f"[EXTRACT-ARTICLE] Mengekstrak artikel dari: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        main_content = soup.find("main") or soup.find("article") or soup.body
        if not main_content:
            logger.warning(f"   Tidak ada konten utama ditemukan di {url}")
            return []
        text = main_content.get_text(separator="\n", strip=True)
        cleaned_text = preprocess_text_with_nlp(text)
        metadata = {
            "source_url": url,
            "content_type": "web_article",
            "title": soup.title.string.strip() if soup.title else "Tanpa Judul"
        }
        return [{"text": cleaned_text, "metadata": metadata}]
    except Exception as e:
        logger.error(f"   Gagal mengekstrak artikel dari {url}. (Error: {e})")
        return []

# ===================================================================
# LANGKAH 2: CHUNKING & PREPROCESSING
# ===================================================================

# [DIUBAH] Fungsi smart_chunk_nodes diganti total dengan Solusi B
def smart_chunk_nodes_semantic(
    nodes: List[Dict[str, Any]], 
    embed_model: HuggingFaceEmbedding,
    breakpoint_percentile: int = 95
) -> List[Dict[str, Any]]:
    """
    DI-UPGRADE: Menggunakan SemanticChunker (Solusi B)
    Memecah node berdasarkan PERUBAHAN MAKNA (topik).
    """
    logger.info(f"[CHUNKING-SEMANTIC] Memulai 'Semantic chunking' pada {len(nodes)} node mentah...")

    # 1. Buat si pemotong "sangat pintar"
    # Dia menggunakan model embedding untuk "merasakan" perubahan topik
    semantic_parser = SemanticSplitterNodeParser(
        embed_model=embed_model,
        breakpoint_percentile_threshold=breakpoint_percentile
    )
    
    docs_to_chunk = []
    final_chunks = [] # Untuk menyimpan dict hasil
    
    # 2. Pisahkan data tabel (wajib) dan konversi sisanya
    for node in nodes:
        # PENTING: Jangan chunking data tabel yang sudah kita proses per baris!
        if node["metadata"]["content_type"] == "web_table_row":
            final_chunks.append(node)
            continue
        
        text = node["text"]
        if not text.strip():
            continue
        
        # Ubah format dict Anda -> LlamaIndex Document
        # SemanticChunker membutuhkan ini
        docs_to_chunk.append(
            Document(text=text, metadata=node["metadata"])
        )

    if not docs_to_chunk:
         logger.warning("   Tidak ada dokumen (non-tabel) untuk di-chunk secara semantik.")
    else:
        # 3. Jalankan chunker pada dokumen (PDF/Artikel)
        logger.info(f"   Memproses {len(docs_to_chunk)} dokumen (PDF/Artikel) dengan SemanticChunker...")
        
        # Ini adalah proses 'pintar' yang membandingkan makna kalimat
        chunked_nodes_objects = semantic_parser.get_nodes_from_documents(docs_to_chunk)
        
        # 4. Konversi balik format LlamaIndex Node -> dict
        for lmi_node in chunked_nodes_objects:
            final_chunks.append({
                "text": lmi_node.get_content(), # .get_content() adalah cara LlamaIndex
                "metadata": lmi_node.metadata   # Metadata tetap terbawa
            })
            
    logger.info(f"   Chunking selesai. Total node akhir: {len(final_chunks)}")
    return final_chunks

def clean_and_hash(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Membersihkan teks akhir dan memberi ID unik.
    (Fungsi ini tidak berubah, sudah bagus)
    """
    logger.info(f"[CLEANING] Membersihkan dan memberi ID pada {len(nodes)} node...")
    cleaned_nodes = []
    for node in nodes:
        cleaned_text = re.sub(r'\s+', ' ', node["text"]).strip()
        if len(cleaned_text) < 20: # Hapus chunk yang terlalu pendek
            continue
        node["id"] = hashlib.md5(cleaned_text.encode("utf-8")).hexdigest()
        node["text"] = cleaned_text
        cleaned_nodes.append(node)
    return cleaned_nodes

# ===================================================================
# LANGKAH 3: EMBEDDING & STORAGE
# ===================================================================

# [DIUBAH] Mengganti SentenceTransformer dengan wrapper LlamaIndex
def get_embedder(model_name=settings.RAG.EMBEDDING_MODEL_NAME):
    """
    Memuat model embedding menggunakan wrapper HuggingFaceEmbedding dari LlamaIndex.
    """
    logger.info(f"[EMBEDDER] Memuat model embedding LlamaIndex: {model_name}")
    # Ini adalah objek LlamaIndex, BUKAN SentenceTransformer
    return HuggingFaceEmbedding(
        model_name=model_name,
        cache_folder=settings.RAG.EMBEDDING_MODEL_PATH,
        trust_remote_code=True, # Sesuai settingan lama Anda
        # device= 'cuda' # Uncomment jika Anda punya GPU
    )

def store_to_qdrant(nodes: List[Dict[str, Any]], embeddings, collection_name: str, batch_size: int = 64):
    """
    Menyimpan/memperbarui node ke Qdrant.
    (Fungsi ini tidak berubah, sudah bagus)
    """
    logger.info(f"[QDRANT] Memulai proses 'upsert' untuk {len(nodes)} node ke koleksi '{collection_name}'...")
    
    try:
        client = QdrantClient(
            url=settings.RAG.QDRANT_URL,
            api_key=settings.RAG.QDRANT_API_KEY,
            timeout=30
        )
        
        embedding_size = len(embeddings[0]) if len(nodes) > 0 else 768
        
        try:
            client.get_collection(collection_name=collection_name)
            logger.info(f"   Koleksi '{collection_name}' sudah ada. Melanjutkan dengan mode 'upsert'.")
        except Exception:
            logger.warning(f"   Koleksi '{collection_name}' tidak ditemukan. Membuat koleksi baru...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=embedding_size, distance=Distance.COSINE)
            )
            logger.info(f"   Koleksi '{collection_name}' berhasil dibuat.")

        total = len(nodes)
        for i in range(0, total, batch_size):
            batch_nodes = nodes[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            
            points = [
                PointStruct(
                    id=node["id"], # Gunakan ID HASH
                    vector=emb, # LlamaIndex sudah memberi list, .tolist() tidak perlu
                    payload={
                        "text": node["text"],
                        "metadata": node["metadata"]
                    },
                )
                for node, emb in zip(batch_nodes, batch_embeddings)
            ]
            
            try:
                client.upsert(
                    collection_name=collection_name, 
                    points=points, 
                    wait=True
                )
                logger.info(f"   Batch {i//batch_size + 1}/{total//batch_size + 1}: simpan {len(points)} node")
            except Exception as e:
                logger.error(f"   Gagal upsert batch (batch {i//batch_size + 1}): {e}")
                
        logger.info(f"\n=== INGESTION BERHASIL: Total {total} node disimpan/diperbarui di '{collection_name}' ===")
        return client

    except Exception as e:
        logger.critical(f"[QDRANT] Gagal terhubung ke Qdrant di {settings.RAG.QDRANT_URL}. Error: {e}")
        return None

# ===================================================================
# MAIN EXECUTION (CONTROL PANEL)
# ===================================================================
if __name__ == "__main__":
    
    # --- KONTROL FILE ANDA ---
    DATA_SOURCES = [
        {"type": "web_article", "url": ""},
        {"type": "web_article", "url": ""},
        {"type": "web_article", "url": ""},
        {"type": "web_article", "url": ""},
        {"type": "web_article", "url": ""},
        {"type": "web_article", "url": ""},
        

        {"type": "web_table", "url": ""},
        {"type": "web_table", "url": ""},
        {"type": "web_table", "url": ""},
        {"type": "web_table", "url": ""},


        {"type": "pdf", "path": os.path.join(root_dir, "data", "")},
        {"type": "pdf", "path": os.path.join(root_dir, "data", "")},
        {"type": "pdf", "path": os.path.join(root_dir, "data", "")},
        {"type": "pdf", "path": os.path.join(root_dir, "data", "")},
        {"type": "pdf", "path": os.path.join(root_dir, "data", "")},
        {"type": "pdf", "path": os.path.join(root_dir, "data", "")},
    ]
    
    COLLECTION_NAME = settings.RAG.COLLECTION_NAME
    
    # [DIUBAH] Variabel chunking lama tidak dipakai, SemanticChunker punya setting sendiri
    # CHUNK_SIZE = 512 
    # CHUNK_OVERLAP = 64
    SEMANTIC_BREAKPOINT = 95 # Sensitivitas (0-100). 95 itu standar.

    logger.info(f"================ STARTING RAG INGESTION ({COLLECTION_NAME}) ================")
    
    all_raw_nodes = []
    
    # === LANGKAH 1: EKSTRAKSI HIBRIDA ===
    for job in DATA_SOURCES:
        try:
            if job.get("url") == "" or job.get("path") == "": continue
            if job["type"] == "pdf":
                all_raw_nodes.extend(extract_pdf(job["path"]))
            elif job["type"] == "web_table":
                all_raw_nodes.extend(extract_web_tables(job["url"]))
            elif job["type"] == "web_article":
                all_raw_nodes.extend(extract_web_article(job["url"]))
        except Exception as e:
            logger.error(f"Gagal memproses job: {job}. Error: {e}")

    if not all_raw_nodes:
        logger.error("\n=== TIDAK ADA DATA UNTUK DIINGEST. Berhenti. ===")
        sys.exit(1)

    try:
        # === [BARU] LANGKAH 2: MEMUAT EMBEDDER (DIPINDAHKAN KE ATAS) ===
        # Semantic Chunker membutuhkan ini SEBELUM chunking
        logger.info("\n[STEP 2] Memuat model embedding (dibutuhkan untuk chunking & encoding)...")
        embedder = get_embedder()

        # === [DIUBAH] LANGKAH 3: CHUNKING & CLEANING ===
        logger.info("\n[STEP 3] Memulai chunking dan pembersihan...")
        chunked_nodes = smart_chunk_nodes_semantic(
            all_raw_nodes, 
            embed_model=embedder,
            breakpoint_percentile=SEMANTIC_BREAKPOINT
        )
        final_nodes = clean_and_hash(chunked_nodes)

        if not final_nodes:
            logger.error("\n=== TIDAK ADA CHUNK VALID SETELAH DIPROSES. Berhenti. ===")
            sys.exit(1)

        logger.info(f"\n[FINAL] Total node siap di-embed: {len(final_nodes)}")

        # === [DIUBAH] LANGKAH 4: EMBEDDING & STORAGE ===
        logger.info("\n[STEP 4] Memulai encoding... (Ini mungkin butuh waktu lama)")
        texts_to_encode = [node["text"] for node in final_nodes]
        
        # [DIUBAH] Kita gunakan method dari 'HuggingFaceEmbedding'
        # Bukan .encode() lagi, tapi .get_text_embedding_batch()
        embeddings = embedder.get_text_embedding_batch(
            texts_to_encode, 
            show_progress_bar=True
        )
        
        logger.info("Encoding selesai.")
        
        client = store_to_qdrant(
            nodes=final_nodes,
            embeddings=embeddings,
            collection_name=COLLECTION_NAME
        )
        logger.info("\n=== INGESTION SELESAI DENGAN AMAN ===")
        
    except Exception as e:
        logger.critical(f"\n=== ERROR KRITIS SAAT INGESTION ===", exc_info=True)
        sys.exit(1)