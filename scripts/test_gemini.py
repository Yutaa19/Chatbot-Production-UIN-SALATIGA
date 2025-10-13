import sys
import os

# Tambahkan root proyek ke Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

from app.core.main import ask_gemini
import os
from dotenv import load_dotenv

load_dotenv()

try:
    ans = ask_gemini(
        system_prompt="Jawab singkat: Halo siapa namamu?",
        user_prompt="Hai saya Andre",
        api_key=os.getenv("GEMINI_API_KEY"),
        model_name="gemini-2.5-flash"
    )
    print("SUKSES:", ans)
except Exception as e:
    print("GAGAL:", e)