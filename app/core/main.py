# app/core/main.py
import re
import logging
from sklearn.metrics.pairwise import cosine_similarity
from qdrant_client.http import models
import google.generativeai as genai
from app.config import settings # <-- AMBIL KONFIGURASI DARI SINI

logger = logging.getLogger(__name__)

# Import klien yang sudah diinisialisasi dari initializer
from app.rag_initializer import get_runtime_components

# Fungsi preprocessing query
def preprocess_query(query):
    """
    Preprocessing query untuk meningkatkan hasil pencarian
    """
    # 1. Convert ke lowercase
    processed = query.lower()
    
    # 2. Hapus karakter khusus tapi pertahankan yang penting
    processed = re.sub(r'[^\w\s\u00C0-\u017F]', ' ', processed)
    
    # 3. Normalisasi whitespace
    processed = re.sub(r'\s+', ' ', processed).strip()
    
    # 4. Untuk bahasa Indonesia, bisa tambah stemming sederhana
    # Misalnya: "pendaftaran" -> "daftar", "penerimaan" -> "terima"
    indonesian_stem = {
        'pendaftaran': 'daftar',
        'penerimaan': 'terima',
        'pengumuman': 'umum',
        'mahasiswa': 'mhs',
        'kampus': 'kampus',
        'universitas': 'univ',
        'fakultas': 'fak',
        'jurusan': 'jur',
        'program': 'prodi',
        'studi': 'prodi'
    }
    
    words = processed.split()
    processed_words = []
    for word in words:
        if word in indonesian_stem:
            processed_words.append(indonesian_stem[word])
        else:
            processed_words.append(word)
    
    return ' '.join(processed_words)

# 6. Improved Similarity Search dengan preprocessing
def search_qdrant(query, client, collection_name, embedder, top_k=3):
    logger.info(f"\n[6] Improved similarity search untuk query: '{query}'")

    try:
        rag = get_runtime_components()
        client = rag['qdrant_client']
        embedder = rag['embedder']
        collection_name = rag['collection_name']
    except Exception as e:
        logger.error(f"[RAG] Failed to load RAG components: {e}")
        return []    
    try:
        # Step 1: Preprocess query
        processed_query = preprocess_query(query)
        logger.info(f"Query processed: '{processed_query}'")
        
        # Step 2: Generate embedding
        query_embedding = embedder.encode([processed_query])[0]
        
        # Step 3: Search dengan top_k yang lebih besar untuk filtering
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_vectors=True
        )
        
        # Step 4: Reranking berdasarkan cosine similarity yang lebih akurat
        if results:
            # Hitung ulang similarity untuk reranking
            vektor_chunks = [hit.vector for hit in results]
            
            # Hitung cosine similarity
            similarities = cosine_similarity([query_embedding], vektor_chunks)[0]
            
            # Reranking berdasarkan similarity score
            reranked_results = []
            for i, hit in enumerate(results):
                reranked_results.append({
                    'text': hit.payload["text"],
                    'score': similarities[i],
                    'original_score': hit.score
                })
            
            # Sort berdasarkan similarity score tertinggi
            reranked_results.sort(key=lambda x: x['score'], reverse=True)
            
            # Ambil top_k terbaik
            final_results = [item['text'] for item in reranked_results[:top_k]]
            
            logger.info(f"Ditemukan {len(final_results)} chunks relevan setelah reranking.")
            logger.info(f"Similarity scores: {[round(item['score'], 3) for item in reranked_results[:top_k]]}")
            
            return final_results
    except Exception as e:
        logger.error(f"Gagal melakukan pencarian di Qdrant: {e}")
        return []



def construct_prompt(query, retrieved_chunks, conversation_history=""):
        """
        Membangun prompt untuk LLM dengan konteks dokumen DAN riwayat percakapan.
        
        Args:
            query (str): Pertanyaan user saat ini
            retrieved_chunks (list): Daftar teks dari hasil retrieval
            conversation_history (str): Riwayat percakapan sebelumnya (opsional)
        """
        logger.info("\n[7] Membangun prompt...")
        
        context = "\n\n".join(retrieved_chunks)
    # Jika ada riwayat, sisipkan; jika tidak, kosongkan
        history_section = f"=== RIWAYAT PERCAKAPAN ===\n{conversation_history}\n" if conversation_history.strip() else ""
        system_prompt = (
        "Anda adalah UINSAGA-AI, asisten resmi UIN Salatiga. "
        "Jawab hanya berdasarkan konteks yang diberikan. "
        "Jika informasi tidak tersedia, katakan: "
        "'Maaf, saya tidak menyajikan informasi ini.Silakan kunjungi uin-salatiga.ac.id untuk info lebih lengkap.' "
        "Sesuaikan gaya bahasa: formal untuk dosen/karyawan, bahasa gen z untuk mahasiswa / calon mahasiswa. "
        "Jawaban harus singkat (maks 2 kalimat), langsung ke inti, dan tidak berulang. "
        "Jangan gunakan salam berbasis waktu dan gunakan sapaan yang sopan dan ramah hanya di awal percakapan."
        )
        user_prompt = f"""
    Pertanyaan user:
    {query}

    Riwayat percakapan sebelumnya (jika ada):
    {history_section}

    Konteks dokumen:
    {context}

    Jawablah dengan gaya asisten UIN Salatiga sesuai instruksi di atas."
    """
        logger.info("Prompt berhasil dibuat.")
        return system_prompt, user_prompt



def ask_gemini(system_prompt: str, user_prompt: str) -> str:
    """
    Kirim prompt ke Google Gemini.
    """
    logger.info(f"[LLM] Calling {settings.GEMINI_MODEL_NAME}...")

    try:
        # ⚙️ Ambil model dari konfigurasi
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=256,
                temperature=0.3,
                top_p=0.9
            ),
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"
            }
        )

        answer = response.text.strip() if response.text else "Maaf, saya tidak dapat menjawab."
        logger.info("[LLM] Response received.")
        return answer

    except Exception as e:
        logger.error(f"[LLM] Gemini call failed: {e}")
        return "Maaf, sedanng terjadi fase pemeliharaan. Silakan coba lagi nanti."              