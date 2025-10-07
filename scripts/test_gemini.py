import os
import sys
import pathlib

# Pastikan path project root ada di sys.path agar import 'app' berhasil
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Gunakan fungsi ask_gemini dari core agar konsisten dengan produksi
from app.core.main import ask_gemini


def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    if not api_key:
        print("ERROR: Environment variable GEMINI_API_KEY belum diset.")
        print("Set terlebih dahulu, contoh (PowerShell):")
        print("  $env:GEMINI_API_KEY = \"<API_KEY_ANDA>\"")
        return 1

    system_prompt = (
        "Anda adalah asisten singkat. Jawab satu kalimat ringkas."
    )
    user_prompt = "Sebutkan nama kampus yang sedang kita bahas."

    try:
        print(f"Menguji panggilan Gemini dengan model: {model}")
        answer = ask_gemini(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            api_key=api_key,
            model_name=model,
        )
        print("\n=== HASIL ===")
        print(answer)
        return 0
    except Exception as e:
        print(f"Gagal memanggil Gemini: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())


