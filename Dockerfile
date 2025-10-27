# =================================================================
# DOCKERFILE UNTUK CHATBOT RAG UIN SALATIGA
# =================================================================

# --- TAHAP 1: BUILDER ---
# Kita gunakan multi-stage build. Tahap 1 hanya untuk meng-install
# dependencies. Ini membuat image akhir kita lebih bersih dan kecil.
# Kita pakai 'slim' (berbasis Debian) karena kompatibilitasnya
# dengan library ML/Data Science (Numpy, Torch, dll) jauh lebih
# baik daripada 'alpine'.
FROM python:3.10-slim AS builder

# Menetapkan direktori kerja di dalam kontainer
WORKDIR /app

# Meng-upgrade pip dan menginstal pustaka build (jika diperlukan)
# Beberapa library Python mungkin perlu C compiler
RUN pip install --upgrade pip && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Salin HANYA file requirements.
# Ini memanfaatkan Docker layer caching. Jika file ini tidak berubah,
# Docker tidak akan meng-install ulang semua library setiap kali build.
COPY requirements.txt .

# Instal semua dependensi Python
RUN pip install --no-cache-dir -r requirements.txt

# --- TAHAP 2: FINAL IMAGE ---
# Ini adalah image yang akan kita gunakan untuk production
FROM python:3.10-slim

# Menetapkan direktori kerja
WORKDIR /app

# (KEAMANAN) Buat grup dan user non-root bernama 'chatbot'
# Menjalankan aplikasi sebagai root di kontainer adalah praktik buruk.
RUN groupadd -r chatbot && useradd --no-log-init -r -g chatbot chatbot

# Salin dependencies yang sudah terinstal dari tahap 'builder'
# Ini adalah inti dari multi-stage build.
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Salin SELURUH kode aplikasi kita (file yg ada di .dockerignore akan diabaikan)
COPY . .

# Berikan kepemilikan file aplikasi ke user 'chatbot'
RUN chown -R chatbot:chatbot /app

# Ganti ke user non-root
USER chatbot

# Memberi tahu Docker bahwa kontainer akan berjalan di port 8000
# (sesuai dengan gunicorn_config.py Anda)
EXPOSE 8000

# Menetapkan environment variable
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Perintah untuk menjalankan aplikasi saat kontainer dimulai.
# Kita gunakan Gunicorn (sesuai file Anda) untuk menjalankan
# aplikasi WSGI (didefinisikan di wsgi.py).
CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:application"]