# scripts/debug_retriever.py
import sys
import os
import logging

# Setup path agar bisa impor 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.rag_initializer import get_runtime_components
    from app.core.main import preprocess_query
    from flask import Flask

    # Kita perlu membuat 'dummy' Flask app context
    # agar 'g' dan 'current_app' (yang dipakai di main.py) bisa berjalan
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)

    def test_retrieval(query: str):
        """
        Fungsi ini hanya menguji Tahap 1: Retrieve (Jaring Ikan)
        """
        print(f"\n--- Menguji Kueri: '{query}' ---")
        
        with app.app_context(): # Masuk ke dummy context
            try:
                # 1. Muat komponen
                rag = get_runtime_components()
                client = rag["qdrant_client"]
                embedder = rag["embedder"]
                collection_name = rag["collection_name"]
                
                # 2. Proses kueri (sama seperti di main.py)
                processed_query = preprocess_query(query)
                query_vec = embedder.encode([processed_query], normalize_embeddings=True)[0]
                
                # 3. Panggil 'search' (Jaring Ikan)
                hits = client.search(
                    collection_name=collection_name,
                    query_vector=query_vec.tolist(),
                    limit=5, # Ambil 5 teratas
                    with_payload=True
                )
                
                if not hits:
                    print("!!! HASIL: Tidak ada dokumen yang ditemukan.")
                    return

                # 4. Tampilkan apa yang ditemukan Qdrant
                print(f"--- Ditemukan {len(hits)} kandidat teratas: ---")
                for i, hit in enumerate(hits):
                    print(f"\n[Kandidat #{i+1}] | Skor Kemiripan (Cosine): {hit.score:.4f}")
                    print("-" * 20)
                    print(hit.payload.get("text", "PAYLOAD KOSONG"))
                    print("\n")

            except Exception as e:
                print(f"!!! ERROR: Gagal menjalankan tes: {e}")

except ImportError as e:
    print(f"Gagal impor: {e}. Pastikan Anda menjalankan dari folder root.")
    sys.exit(1)
except Exception as e:
    print(f"Error saat setup: {e}")
    sys.exit(1)

# --- JALANKAN TES ---
if __name__ == "__main__":
    # Tes kueri Anda yang gagal
    test_retrieval("berapa ukt prodi sains data?")
    
    # Tes kueri lain untuk perbandingan
    test_retrieval("berapa ukt prodi bisnis digital?")