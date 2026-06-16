import os
from google import genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def estimate_flood_depth(image_path):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
        
    try:
        client = genai.Client(api_key=api_key.strip())
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((800, 800))
        
        # PROMPT BARU YANG LEBIH TEGAS
        prompt = """Kamu adalah sistem analisis mitigasi bencana. Analisis gambar ini.
        ATURAN MUTLAK:
        1. Jika ada genangan air di jalan, jawab HANYA dengan angka kedalaman dalam cm (contoh: 40).
        2. Jika jalanan kering/aman, jawab dengan teks: KERING
        3. Jika gambar adalah foto wajah, dalam ruangan, atau TIDAK ada unsur jalanan sama sekali, jawab dengan teks: SPAM"""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt, img]
        )
        
        response_text = response.text.strip().upper()
        
        # FILTER KONDISI TEKS DULU
        if "SPAM" in response_text:
            return -1
        if "KERING" in response_text:
            return 0
            
        # JIKA BUKAN TEKS, BARU AMBIL ANGKA
        angka_saja = ''.join(filter(str.isdigit, response_text))
        if angka_saja:
            return int(angka_saja)
            
        return None
    except Exception as e:
        print(f"Error AI: {e}")
        return None