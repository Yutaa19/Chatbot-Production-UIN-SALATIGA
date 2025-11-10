🛡️ Dokumentasi API Admin (admin.py)
1. Ikhtisar
File app/api/admin.py menyediakan serangkaian endpoint internal untuk pemantauan dasar dan pemeliharaan aplikasi chatbot. Endpoint ini tidak dimaksudkan untuk penggunaan publik dan dilindungi oleh dua lapisan keamanan.

2. Model Keamanan
Akses ke endpoint /api/admin/* diamankan secara ketat:

Level Server (Nginx): Endpoint ini diblokir dari internet. Konfigurasi nginx.conf (di server) secara eksplisit menolak semua koneksi ke /api/admin.

Level Aplikasi (Flask): Setiap endpoint di dalam file ini memanggil fungsi require_admin_auth(). Fungsi ini memeriksa header HTTP X-Admin-Secret dan mencocokkannya dengan variabel ADMIN_SECRET_KEY dari file .env Anda.

3. Cara Mengakses (Wajib via SSH Tunnel)
Satu-satunya cara aman untuk mengakses endpoint ini adalah dari laptop Anda dengan membuat "terowongan rahasia" (SSH Tunnel) ke server.

Langkah 1: Buat SSH Tunnel (di Laptop Anda)
Buka terminal di laptop Anda dan jalankan perintah ini. Ini akan meneruskan port 8080 di laptop Anda ke port 8000 (port Gunicorn/Docker) di server.

# Ganti 'chatbot@chatbot.uinsalatiga.ac.id' dengan user & host server Anda
"ssh -L 8080:localhost:8000 chatbot@chatbot.uinsalatiga.ac.id"

Langkah 2: Gunakan curl (di Laptop Anda)
Buka terminal baru di laptop Anda. Anda sekarang dapat "berbicara" dengan http://localhost:8080 seolah-olah Anda berada di dalam server.

PENTING: Ganti <ADMIN_SECRET_KEY_ANDA> dengan nilai dari file .env di server Anda.

4. Referensi Endpoint
GET /api/admin/stats
Fungsi: get_stats(). Memberikan statistik dasar dari Redis untuk memantau aktivitas dan penggunaan memori.

Perintah curl (dari Laptop):

curl -X GET http://localhost:8080/api/admin/stats \
     -H "X-Admin-Secret: <ADMIN_SECRET_KEY_ANDA>"

Respons Sukses (Contoh):

{
  "status": "ok",
  "active_users": 150,
  "redis_memory_mb": 2.45,
  "redis_keys": 305,
  "note": "Statistik riil memerlukan logging tambahan. Ini adalah estimasi dasar."
}

active_users: Estimasi jumlah sesi obrolan yang sedang aktif (berdasarkan jumlah kunci chat:*).

redis_memory_mb: Total memori yang digunakan oleh Redis.

POST /api/admin/cache/reset
Fungsi: reset_cache(). Menghapus semua cache jawaban RAG (kunci yang berawalan rag:resp:*). Ini wajib dilakukan setelah Anda memperbarui knowledge base (Qdrant) agar chatbot tidak memberikan jawaban lama.

Perintah curl (dari Laptop):
curl -X POST http://localhost:8080/api/admin/cache/reset \
     -H "X-Admin-Secret: <ADMIN_SECRET_KEY_ANDA>"

Respons Sukses (Contoh):
{
  "message": "Cache berhasil direset. 120 entri dihapus."
}

GET /api/admin/history/<user_id>
Fungsi: get_user_history(user_id). Mengambil riwayat percakapan lengkap untuk user_id tertentu. Sangat berguna untuk men-debug mengapa pengguna mendapatkan jawaban yang aneh.

Catatan: Anda bisa mendapatkan user_id (biasanya UUID) dari log aplikasi (docker-compose logs app) atau dari database analitik PostgreSQL Anda.

Perintah curl (dari Laptop):
# Ganti <USER_ID_DARI_LOG> dengan ID pengguna yang ingin Anda lacak
curl -X GET http://localhost:8080/api/admin/history/<USER_ID_DARI_LOG> \
     -H "X-Admin-Secret: <ADMIN_SECRET_KEY_ANDA>"

Respons Sukses (Contoh):

{
  "user_id": "abc-123-def-456",
  "history": [
    {
      "role": "user",
      "content": "Apa visi UIN Salatiga?"
    },
    {
      "role": "assistant",
      "content": "Visi UIN Salatiga adalah menjadi universitas unggul..."
    }
  ]
}
