Dokumentasi Deployment Final (Pilot 3 Bulan) - UINSAGA-AI

    "Tahap 1: Setup Server (Infra & Keamanan)"
        A(1. Install: Nginx, Docker, UFW, Certbot) --> B(2. Konfigurasi Firewall UFW: Izinkan port 22, 80, 443);
        B --> C(3. Jalankan 'certbot' untuk dapat SSL/HTTPS);
        C --> D(4. Edit 'nginx.conf': Atur 'proxy_pass' ke 127.0.0.1:8000);
        D --> E(5. Restart Nginx: 'systemctl restart nginx');
    end
    
    "Tahap 2: Setup Aplikasi (Docker)"
        E --> F(6. Buat user 'chatbot' & folder '/home/chatbot/uinsaga-ai');
        F --> G(7. Buat 2 file di dalam folder: 'docker-compose.yml' & '.env');
        G --> H(8. Isi '.env' dengan semua Kunci Rahasia);
    end
    
    "Tahap 3: Menjalankan Aplikasi (Mesin)"
        H -- 9. (Opsional) Jalankan 'docker login' --> I(10. Jalankan 'docker pull <nama_image_anda>');
        H --> I;
        I --> J(11. Jalankan 'docker-compose up -d');
    end
    
   "Tahap 4: Koneksi Frontend (Selesai)"
        J --> K(12. Server Siap Menerima Trafik);
        K -- 13. (Di WordPress) --> L(Tempel 'widget.html' ke WordPress UIN);
        L --> M(✅ Chatbot Live);
   end
   
1. Pendahuluan
Dokumen ini merinci langkah-langkah teknis untuk men-deploy aplikasi UINSAGA-AI Chatbot di server UIN Salatiga.

Arsitektur Deployment (Direkomendasikan): Alur kerja ini memisahkan "pembangun" (Developer) dari "penjalan" (Server).

Developer : Mem-build image Docker di komputer Anda dan mem-push ke sebuah Image Registry (seperti Docker Hub atau Google Artifact Registry).

Server (UIN): Men-pull image yang sudah jadi tersebut dari Registry, lalu menjalankannya menggunakan docker-compose.

Langkah 2: Penyiapan Server & Perisai (Nginx + Firewall)
Pelaksana: Admin Server UIN

"sudo apt update"
"sudo apt install nginx docker.io docker-compose -y"


Konfigurasi Firewall (UFW):
"sudo ufw allow 'Nginx Full'"  # Port 80 & 443
"sudo ufw allow 22/tcp"       # Ganti jika port SSH kustom
"sudo ufw enable"

Instal SSL (Let's Encrypt):
"sudo apt install certbot python3-certbot-nginx -y"
# Ganti dengan domain Anda
"sudo certbot --nginx -d chatbot.uinsalatiga.ac.id"


konfigurasi Nginx (Reverse Proxy):

Edit file konfigurasi Nginx (misal: /etc/nginx/sites-available/default):

Nginx :
location / {
    proxy_pass http://127.0.0.1:8000; # Arahkan ke Docker
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 90s; # Timeout untuk LLM
}

Tes dan restart Nginx:
sudo nginx -t
sudo systemctl restart nginx

Menyiapkan & Menjalankan "Mesin" (Docker)

Buat Direktori & File Konfigurasi
Buat user dan direktori untuk aplikasi:

    sudo adduser chatbot
    sudo usermod -aG docker chatbot # Izinkan user ini menjalankan Docker
    sudo mkdir -p /home/chatbot/uinsaga-ai
    sudo chown -R chatbot:chatbot /home/chatbot/uinsaga-ai

Login sebagai user chatbot:

    su - chatbot
    cd /home/chatbot/uinsaga-ai

Buat file docker-compose.yml (Server HANYA butuh file ini):

# ===================================================================
# DOCKER-COMPOSE.YML (FINAL - UNTUK SERVER)
# ===================================================================
version: '3.8'

services:
  # 1. LAYANAN APLIKASI CHATBOT
  app:
    # PENTING: Tarik image yang sudah Anda push
    image: yutaa19/uinsaga-chatbot:v1.0 # <-- GANTI DENGAN NAMA IMAGE ANDA
    container_name: chatbot_app
    restart: always
    env_file:
      - .env
    ports:
      - "127.0.0.1:8000:8000" # Hanya terekspos ke Nginx (localhost)
    depends_on:
      - db
    networks:
      - chatbot-net

  # 2. LAYANAN DATABASE (POSTGRESQL UNTUK ANALYTICS)
  db:
    image: postgres:15-alpine
    container_name: chatbot_pg_db
    restart: always
    env_file:
      - .env
    volumes:
      - pg_data:/var/lib/postgresql/data
    networks:
      - chatbot-net # Tidak terekspos ke publik

networks:
  chatbot-net:
    driver: bridge

volumes:
  pg_data:
    driver: local


Buat file rahasia .env:
"nano .env"

Tarik (Pull) dan Jalankan
(Jika image Anda private) Login ke Docker Registry:

Tarik (Pull) Image chatbot:

"docker pull yutaa19/uinsaga-chatbot:v1.0"

Jalankan:

"docker-compose up -d"

