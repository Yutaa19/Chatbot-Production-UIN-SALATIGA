# 🤖 UIN Salatiga RAG Chatbot

Chatbot AI resmi Universitas Islam Negeri (UIN) Salatiga yang menjawab pertanyaan berdasarkan dokumen internal kampus.

## Fitur
- Jawaban berbasis knowledge base resmi UIN
- Mendukung pertanyaan tentang: Seputar Uin Salatiga
- Cepat berkat caching Redis
- Aman dan hemat biaya

## Teknologi
- **Backend**: Python Flask + Gunicorn
- **Vector DB**: Qdrant (self-hosted)
- **Embedding**: `firqaaa/indo-sentence-bert-base`
- **LLM**: Google Gemini 2.0 Flash-lite
- **Cache**: Redis
- **Deployment**: Server Uin

## Deployment
Hanya untuk tim IT internal UIN Salatiga.  
Lihat `docs/DEPLOYMENT.md` untuk panduan lengkap.

## Lisensi
© 2025 Universitas Islam Negeri Salatiga  
Hak cipta dilindungi undang-undang.

