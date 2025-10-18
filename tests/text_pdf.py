# test_pdf.py
from llama_index.readers.file import PDFReader
from pathlib import Path

loader = PDFReader()
docs = loader.load_data(file=Path("data/Struktur Organisasi Kampus UIN SALATIGA.pdf"))

print("Jumlah dokumen:", len(docs))
for i, doc in enumerate(docs):
    print(f"\n--- Halaman {i+1} ---")
    print(doc.text[:500])  # tampilkan 500 karakter pertama