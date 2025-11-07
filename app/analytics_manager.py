# app/analytics_manager.py
import psycopg2
import psycopg2.pool
import logging
from app.config import settings

# Buat "kolam koneksi" (Connection Pool)
# Ini JAUH LEBIH EFISIEN daripada membuka-tutup koneksi setiap chat.
# Kita membuat "kolam" berisi koneksi yang siap pakai.
try:
    pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,  # Cukup untuk traffic awal
        dsn=settings.DATABASE_URL
    )
    logging.info("Kumpulan koneksi PostgreSQL berhasil dibuat.")
except Exception as e:
    logging.error(f"Gagal membuat kumpulan koneksi PostgreSQL: {e}")
    pool = None

def init_db():
    """
    Fungsi ini untuk membuat tabel 'chat_interactions' jika belum ada.
    Anda bisa menjalankannya sekali dari skrip terpisah.
    """
    if not pool:
        logging.error("Tidak ada kumpulan koneksi. Gagal inisialisasi DB.")
        return
        
    # Ambil satu koneksi dari "kolam"
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_interactions (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    user_query TEXT NOT NULL,
                    bot_response TEXT,
                    retrieval_source VARCHAR(50),
                    llm_model VARCHAR(100),
                    input_tokens INT,
                    output_tokens INT,
                    latency_ms INT
                );
            """)
            conn.commit()  # Simpan perubahan
            logging.info("Tabel 'chat_interactions' berhasil diperiksa/dibuat.")
    except Exception as e:
        logging.error(f"Gagal membuat tabel: {e}")
    finally:
        # Kembalikan koneksi ke "kolam" agar bisa dipakai lagi
        pool.putconn(conn)

def log_interaction(session_id, query, response, source, model, in_tokens, out_tokens, latency):
    """Fungsi utama untuk mencatat setiap interaksi chat."""
    if not pool:
        logging.error("Tidak ada kumpulan koneksi. Gagal mencatat interaksi.")
        return

    sql = """
        INSERT INTO chat_interactions 
        (session_id, user_query, bot_response, retrieval_source, llm_model, input_tokens, output_tokens, latency_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            # Menggunakan parameterisasi (%s) adalah WAJIB.
            # Ini secara otomatis melindungi Anda dari serangan SQL Injection.
            cur.execute(sql, (
                session_id, query, response, source, model, in_tokens, out_tokens, latency
            ))
            conn.commit()
    except Exception as e:
        logging.error(f"Gagal mencatat log ke DB: {e}")
    finally:
        pool.putconn(conn)