# install_nltk.py
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Mengunduh data NLTK 'punkt'...")
    nltk.download('punkt')
    print("Berhasil!")