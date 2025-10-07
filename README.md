# 🤖 UIN Salatiga RAG Chatbot

Chatbot AI resmi Universitas Islam Negeri (UIN) Salatiga yang menjawab pertanyaan berdasarkan dokumen internal kampus.

## Fitur
- Jawaban berbasis knowledge base resmi UIN
- Mendukung pertanyaan tentang: visi, misi, logo, bendera, pimpinan, akreditasi, kehidupan kampus
- Cepat berkat caching Redis
- Aman dan hemat biaya

## Teknologi
- **Backend**: Python Flask + Gunicorn
- **Vector DB**: Qdrant (self-hosted)
- **Embedding**: `all-MiniLM-L6-v2`
- **LLM**: Google Gemini 1.5 Flash
- **Cache**: Redis
- **Deployment**: VPS Hostinger (KVM2)

## Deployment
Hanya untuk tim IT internal UIN Salatiga.  
Lihat `docs/DEPLOYMENT.md` untuk panduan lengkap.

## Lisensi
© 2025 Universitas Islam Negeri Salatiga  
Hak cipta dilindungi undang-undang.

