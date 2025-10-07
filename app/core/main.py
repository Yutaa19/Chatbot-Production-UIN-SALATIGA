import uuid
import re
from pathlib import Path
from llama_index.readers.file import PDFReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from qdrant_client.http import models
import google.generativeai as genai
import requests
import json
from dotenv import load_dotenv
import os

# Muat variabel lingkungan dari .env
load_dotenv()

# 1. Ekstraksi PDF
def extract_text_from_pdf_llamaindex(pdf_path):
    """
    Mengekstrak teks dari file PDF menggunakan LlamaIndex.
    """
    print("\n[1] Ekstraksi PDF dengan LlamaIndex...")
    
    # PDFReader hanya membaca dari direktori, bukan file tunggal.
    # Jadi, kita perlu menempatkan file PDF ke dalam daftar.
    loader = PDFReader()  # Buat OBJEK dulu
    documents = loader.load_data(file=Path(pdf_path))  # Panggil dari OBJEK
    
    full_text = "\n".join([doc.text for doc in documents])
        
    page_count = len(documents)
    print(f"Ekstraksi selesai, total {page_count} dokumen (file).")
    
    return full_text

# 1.1 Ekstraksi dari Web
def extract_text_from_web_async(urls):
    from llama_index.readers.web import TrafilaturaWebReader
    """
    Mengekstrak teks dari daftar URL secara async menggunakan TrafilaturaWebReader.
    """
    print(f"\n[1.1] Ekstraksi dari {len(urls)} URL (async)...")
    
    reader = TrafilaturaWebReader()
    documents = reader.load_data(urls=urls)  # Mendukung async secara internal
    
    full_text = "\n".join([doc.text for doc in documents])
    
    print("Ekstraksi web selesai.")
    return full_text

def clean_text(raw_text):
    print("\n[2] Cleansing text...")
    
    # 1. Hapus atau ganti tanda ** (bold markdown)
    # Ganti **teks** jadi teks (hapus bold-nya)
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', raw_text)
    
    # 2. Bersihkan whitespace berlebih (spasi, tab, enter)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 3. Potong spasi di awal & akhir
    cleaned = cleaned.strip()
    
    print("Cleansing selesai, panjang teks:", len(cleaned))
    return cleaned

# 3. Chunking
def chunk_text(text, chunk_size=500, overlap=100):
    print("\n[3] Chunking text...")
    chunks, start, text_length = [], 0, len(text)
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    print(f"Chunking selesai, total {len(chunks)} chunks.")
    return chunks

# 4. Embedding dengan MiniLM v2
def get_embedder(model_name="firqaaa/indo-sentence-bert-base"):
    print("\n[4] Loading embedding model:", model_name)
    return SentenceTransformer(model_name)

# 5. Store ke Qdrant
from qdrant_client.http import models

def store_to_qdrant(chunks, embeddings, qdrant_url, api_key, collection_name, batch_size=50):
    print("\n[5] Menyimpan embedding ke Qdrant...")

    client = QdrantClient(url=qdrant_url, api_key=api_key, timeout=30)

    # === RECREATE COLLECTION (HAPUS + BUAT BARU DALAM 1 LANGKAH) ===
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=len(embeddings[0]),
            distance=Distance.COSINE
        )
    )
    print(f"Collection '{collection_name}' berhasil dibuat/diganti dengan dimensi: {len(embeddings[0])}")

    # === SIMPAN DATA ===
    total = len(chunks)
    for i in range(0, total, batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={"text": chunk},
            )
            for chunk, embedding in zip(batch_chunks, batch_embeddings)
        ]
        client.upsert(collection_name=collection_name, points=points)
        print(f" Batch {i//batch_size + 1}: simpan {len(points)} chunks")

    print(f"Sukses simpan {total} chunks ke collection '{collection_name}'")
    return client 

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
def search_qdrant(query, client, collection_name, embedder, top_k=5):
    from sklearn.metrics.pairwise import cosine_similarity
    print(f"\n[6] Improved similarity search untuk query: '{query}'")
    
    # Step 1: Preprocess query
    processed_query = preprocess_query(query)
    print(f"Query processed: '{processed_query}'")
    
    # Step 2: Generate embedding
    query_embedding = embedder.encode([processed_query])[0]
    
    # Step 3: Search dengan top_k yang lebih besar untuk filtering
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding,
        limit=top_k * 2,
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
        
        print(f"Ditemukan {len(final_results)} chunks relevan setelah reranking.")
        print(f"Similarity scores: {[round(item['score'], 3) for item in reranked_results[:top_k]]}")
        
        return final_results
    else:
        print("Tidak ditemukan chunks relevan.")
        return []



def construct_prompt(query, retrieved_chunks, conversation_history=""):
    """
    Membangun prompt untuk LLM dengan konteks dokumen DAN riwayat percakapan.
    
    Args:
        query (str): Pertanyaan user saat ini
        retrieved_chunks (list): Daftar teks dari hasil retrieval
        conversation_history (str): Riwayat percakapan sebelumnya (opsional)
    """
    print("\n[7] Membangun prompt...")
    
    context = "\n\n".join(retrieved_chunks)
 # Jika ada riwayat, sisipkan; jika tidak, kosongkan
    history_section = f"=== RIWAYAT PERCAKAPAN ===\n{conversation_history}\n" if conversation_history.strip() else ""
    system_prompt = (
        "Anda adalah UINSAGA-AI, sebuah asisten virtual dan customer service yang ramah, sopan, dan beretika tinggi, khusus untuk melayani seluruh pertanyaan seputar UIN Salatiga.. "
        "Fokus utama Anda adalah membantu berbagai pihak, mulai dari calon mahasiswa (siswa SMA/luar negeri), mahasiswa aktif, orang tua/wali murid, dosen, Karyawan dan Staf Administrasi, Rektor dan Jajaran Manajemen dengan menjawab pertanyaan mereka secara akurat dan profesional. "
        "Gunakan Bahasa yang Relevan: Sesuaikan gaya bahasa Anda dengan audiens.. "
        "Untuk siswa SMA/calon mahasiswa Gunakan bahasa yang jelas, lugas, dan menarik. Berikan informasi yang memotivasi mereka untuk bergabung dengan UIN Salatiga dan jangan terlalu panjang teks nya simple saja."
        "Untuk mahasiswa aktif, dosen, dan karyawan atau staff Gunakan bahasa yang formal dan informatif, fokus pada detail teknis terkait prosedur atau data akademik,kemahasiswaan, dan keuangan."
        "Untuk orang tua atau wali Gunakan bahasa yang meyakinkan, sopan, dan mudah dipahami, memberikan rasa aman dan kepercayaan"
        "Sumber Informasi Seluruh jawaban Anda harus didasarkan pada konteks yang diberikan di bawah ini. Jangan pernah menggunakan pengetahuan umum atau informasi lain di luar konteks yang tersedia."
        "Jika jawaban ditemukan, berikan jawaban yang singkat, padat, dan langsung ke inti permasalahan."
        "Jika jawaban tidak ditemukan di dalam konteks, jawab dengan sopan, dan berikan permohonan maaf untuk informasi lebih lanjut ada di portal uin salatiga untuk informasi lebih lengkap."
        "Tindakan Tambahan: Jika pertanyaan mengarah pada data spesifik (misalnya, jadwal mata kuliah atau nama dosen) jika jawaban di temukan jawab dengan singkat padat jelas sesuai data yang ada jika tidak ada jawaban sarankan pengguna untuk mengecek aplikasi smart mhs atau SIAKAD UIN SALATIGA."
        "Janagan memakai salam yang berhubungan waktu seperti selamat pagi siang sore malam dan berikan salam pada saat user pertama kali bertanya selebih nya jawab pertanyaan dengan jawaban yang relevan."
        "Anda diharapkan memiliki pemahaman mendalam tentang terminologi akademis, keuangan, dan kemahasiswaan yang berlaku di UIN Salatiga."
        "setiap anda menjawab pertanyaan jawablah dengan simple dan singkat jangan terlalu panjang. teks nya langsung kepada inti nya dan ini berlaku pada setiap pertanyaan user yang ada "
        "ketika user menanyakan pertanyaan ringan atau mengobrol ngobrol curhatan mereka maka anda dapat menjawab dengan sesuai dengan pertanyaan user dengan bahasa gen z yang singkat dan padat dan langsung Call To action untuk menanyakan seputar Uin salatiga dengan ramah dan sopan ya."
    )
    user_prompt = f"""
Pertanyaan user:
{query}

Riwayat percakapan sebelumnya (jika ada):
{history_section}

Konteks dokumen:
{context}

Jawablah dengan gaya seorang CS dan gunakan pengetahuan tambahan dari internet jika perlu dan jadilah customer service international yang di gunakan perusahaan seperti apple nvidia google microsoft dan openAi jika ingin memberikan salam hangat seperti"Selamat malam /siang/pagi gunakan salam yang sesuai dengan waktu user bertanya"
"""
    print("Prompt berhasil dibuat.")
    return system_prompt, user_prompt



def ask_gemini(system_prompt, user_prompt, api_key, model_name="gemini-1.5-flash"):
    print(f"\n[8] Mengirim prompt ke {model_name} (via Google AI Studio)...")
    
    # Konfigurasi API key
    genai.configure(api_key=api_key)
    
    # Buat instance model
    model = genai.GenerativeModel(model_name)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=256,    # BATAS KETAT UNTUK HEMAT BIAYA
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
        return response.text.strip() if response.text else "Maaf, saya tidak dapat menjawab."
    except Exception as e:
        raise ConnectionError(f"Gagal memanggil Gemini: {str(e)}")

# MAIN PIPELINE
if __name__ == "__main__":
    # --- konfigurasi ---
    PDF_FILE = "sejarah_uin.pdf"

    urls_list = [
    # Daftar URL Anda
    "https://www.uinsalatiga.ac.id/#",
    "https://www.uinsalatiga.ac.id/tentang-uin-salatiga/",
    "https://www.uinsalatiga.ac.id/kehidupan-kampus/",
    "https://www.uinsalatiga.ac.id/visi-dan-misi/",
    "https://www.uinsalatiga.ac.id/logo/",
    "https://www.uinsalatiga.ac.id/bendera/",
    "https://www.uinsalatiga.ac.id/mars-dan-hymne/",
    "https://www.uinsalatiga.ac.id/akreditasi/",
    "https://www.uinsalatiga.ac.id/akreditasi-program-studi/",
    "https://www.uinsalatiga.ac.id/pimpinan/#",
    "https://www.uinsalatiga.ac.id/struktur-organisasi/",
    "https://www.uinsalatiga.ac.id/tenaga-pendidik/",
    "https://www.uinsalatiga.ac.id/tenaga-kependidikan/",
    ]
    
    
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL")
    # === PETA ENDPOINT API KAMPUS (GANTI SESUAI DOKUMENTASI RESMI) ===

    # --- ekstraksi dan gabungkan PDF + Web ---
    print("\n[1.2] Menggabungkan teks dari PDF dan Web...")
    pdf_text = extract_text_from_pdf_llamaindex(PDF_FILE)
    web_text = extract_text_from_web_async(urls_list)
    
    # Logging debug
    print(f"[DEBUG] Panjang teks PDF: {len(pdf_text)} karakter")
    print(f"[DEBUG] Panjang teks Web: {len(web_text)} karakter")
    
    # Gabungkan jika web_text tidak kosong
    if not web_text.strip():
        print("Peringatan: Hasil ekstraksi web kosong. Hanya menggunakan PDF.")
        combined_text = pdf_text
    else:
        combined_text = pdf_text + "\n\n=== TEKS DARI WEB ===\n\n" + web_text

    print(f"[DEBUG] Panjang teks Gabungan: {len(combined_text)} karakter")
    cleaned_text = clean_text(combined_text)
    chunks = chunk_text(cleaned_text, chunk_size=500, overlap=100)

    # --- embedding & store ---
    embedder = get_embedder()
    embeddings = embedder.encode(chunks, convert_to_tensor=False)
    client = store_to_qdrant(chunks, embeddings, QDRANT_URL, QDRANT_API_KEY, COLLECTION_NAME)

    # --- loop query user ---
    print("\nSistem siap! Ketik pertanyaan Anda (atau 'exit' untuk keluar).")
    while True:
        user_query = input("\nPertanyaan: ")
        if user_query.lower() in ["exit", "quit"]:
            print("Program selesai.")
            break

        #preprocess & embedding query
        query_clean = preprocess_query(user_query)
        print(f"[DEBUG] Query setelah preprocessing: '{query_clean}'")

        # similarity search

        retrieved = search_qdrant(query_clean, client, COLLECTION_NAME, embedder, top_k=3)
        print("\n=== Retrieved Chunks ===")
        for i, chunk in enumerate(retrieved, 1):
            print(f"[{i}] {chunk[:200]}...\n")

        # construct prompt
        # === Construct Prompt - SERTAKAN RIWAYAT! ===
        system_prompt, user_prompt = construct_prompt(
            query=user_query,
            retrieved_chunks=retrieved,
            conversation_history=""  # Tidak ada riwayat di mode CLI
        )

        answer = ask_gemini(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        api_key=GEMINI_API_KEY,
        model_name=GEMINI_MODEL
        )
        print("\n=== Jawaban CS ===")
        print(answer)
