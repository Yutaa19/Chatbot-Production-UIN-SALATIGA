# gunicorn_config.py (REVISI FINAL - Performa Tinggi)
import os

# --- KONEKSI ---
# WAJIB '0.0.0.0' agar bisa menerima koneksi dari host Docker
bind = "0.0.0.0:8000"

# --- PERFORMA (INI KUNCINYA) ---

# 1. Worker Class: 'gevent'
#    Kita pakai 'gevent' (yang sudah diinstal)
#    Ini adalah worker 'ajaib' yang non-blocking.
worker_class = "gevent"

# 2. Workers: (Jumlah Koki)
#    Ini adalah jumlah prosesor (CPU) yang dipakai.
#    '2' sudah cukup untuk memulai di server 2 vCPU.
workers = 2

# 3. Worker Connections: (Jumlah Tangan per Koki)
#    INI YANG AKAN MENANGANI 500 PERMINTAAN BERSAMAAN.
#    Artinya, SETIAP 1 worker bisa menangani 1000 koneksi
#    yang sedang "menunggu" (I/O bound) secara bersamaan.
worker_connections = 1000

# 4. Pengaturan Lainnya
timeout = 90         # Waktu tunggu maks untuk 1 request (menunggu Gemini)
keepalive = 5
max_requests = 400
max_requests_jitter = 40
preload_app = False
worker_tmp_dir = "/dev/shm"

# --- LOGGING (Standar Docker) ---
# Mengirim log ke STDOUT/STDERR agar 'docker logs' bisa menangkapnya
loglevel = "info"
capture_output = True 

# --- SECURITY ---
# (Opsional) Dockerfile kita sudah menangani ini
user = "chatbot"
group = "chatbot"