# scripts/init_database.py
import sys
import os
import logging

# Trik untuk menambahkan 'app' ke path agar kita bisa impor
# (Ini mengasumsikan skrip dijalankan dari folder root proyek)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Sekarang kita bisa impor dari 'app'
try:
    from app.analytics_manager import init_db

    # Konfigurasi logging dasar agar kita bisa lihat output
    logging.basicConfig(level=logging.INFO)
    logging.info("Memulai inisialisasi database...")

    # Panggil fungsi untuk membuat tabel
    init_db()

    logging.info("Inisialisasi database selesai. Tabel 'chat_interactions' seharusnya sudah siap.")

except ImportError as e:
    logging.error(f"Gagal mengimpor modul: {e}")
    logging.error("Pastikan Anda menjalankan skrip ini dari folder root proyek (Pra Production).")
except Exception as e:
    logging.error(f"Terjadi error saat inisialisasi database: {e}")