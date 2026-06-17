import os
import io
from google import genai
from PIL import Image
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 1. FUNGSI HELPER: Khusus menembak API dan di-backup oleh auto-retry
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_ai_vision(prompt, img):
    return client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[prompt, img]
    )

# 2. FUNGSI UTAMA: Pemrosesan gambar dan logika kedalaman
def estimate_flood_depth(image_file):
    try:
        # BACA LANGSUNG DARI RAM: Ubah file Django menjadi wujud Byte, 
        # lalu corongkan ke dalam PIL Image. Dijamin 100% anti crash!
        img_bytes = image_file.read()
        img = Image.open(io.BytesIO(img_bytes))
        
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((800, 800))

        prompt = """
        Kamu adalah sistem analisis mitigasi bencana. Analisis gambar ini.

        ATURAN MUTLAK:
        1. Jika ada genangan air di jalan, jawab HANYA dengan angka kedalaman dalam cm (contoh: 40).
        2. Jika jalanan kering/aman, jawab dengan teks: KERING
        3. Jika gambar adalah foto wajah, dalam ruangan, atau TIDAK ada unsur jalanan sama sekali, jawab dengan teks: SPAM
        """

        # Panggil fungsi helper
        response = fetch_ai_vision(prompt, img)

        response_text = response.text.strip().upper()

        if "SPAM" in response_text:
            return -1

        if "KERING" in response_text:
            return 0

        angka_saja = ''.join(filter(str.isdigit, response_text))

        if angka_saja:
            return int(angka_saja)

        return None

    except Exception as e:
        print(f"Error AI: {e}")
        return None