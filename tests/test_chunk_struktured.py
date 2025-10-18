import re
import nltk

def normalize_jabatan(text: str) -> str:
    """Normalisasi teks struktur jabatan."""
    text = re.sub(r'[:=]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def smart_chunk_semantic(text: str, max_chunk_size: int = 512, overlap: int = 64) -> list:
    """Chunk berbasis batas kalimat (NLP-aware)."""
    if not text.strip():
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        sentences = nltk.sent_tokenize(para)
        for sent in sentences:
            test = (current_chunk + " " + sent).strip()
            if len(test) <= max_chunk_size or not current_chunk:
                current_chunk = test
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk)

    # Tambahkan overlap
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
            else:
                prev_words = chunks[i-1].split()[-overlap//5:]
                new_chunk = " ".join(prev_words + chunk.split())
                overlapped.append(new_chunk)
        chunks = overlapped
    return chunks

def chunk_structured_document(text: str) -> list:
    """Chunk per baris untuk dokumen struktural (jabatan, SOP, dll)."""
    lines = text.splitlines()
    chunks = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Deteksi pola struktur: mengandung = atau : atau kata kunci jabatan
        if re.search(r'[=:]', line) or any(kw in line for kw in ["Rektor", "Dekan", "Wakil Rektor", "Kepala", "Direktur", "Ketua"]):
            if buffer:
                chunks.append(normalize_jabatan(buffer))
            buffer = line
        else:
            buffer += " " + line if buffer else line
    if buffer:
        chunks.append(normalize_jabatan(buffer))
    return chunks