import os
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def estimate_flood_depth(image_path):
    try:
        img = Image.open(image_path)

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

        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content([prompt, img])

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