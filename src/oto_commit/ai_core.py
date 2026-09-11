import json
import urllib.request
import urllib.error
from .config import load_api_key

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
TIMEOUT_SECONDS = 30

def generate_commit_message(diff_text: str) -> str:
    api_key = load_api_key()
    
    if not api_key:
        return "HATA: API anahtarı bulunamadı. Lütfen 'oto-commit ayar' komutunu çalıştırın veya GEMINI_API_KEY ortam değişkenini tanımlayın."

    prompt = f"""
    Sen kıdemli bir yazılım mühendisisin. Aşağıdaki git diff çıktısını analiz et.
    Değişikliklerin asıl amacını kavrayarak, Conventional Commits (feat:, fix:, chore:, refactor:, docs: vb.) formatına uygun, açıklayıcı, şık ve tam profesyonel tek bir Türkçe cümle yaz.
    Sadece üretilen commit mesajını ver.
    
    {diff_text}
    """
    
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode('utf-8')
    
    try:
        # Anahtar URL yerine header'da taşınır; böylece proxy/erişim loglarına düşmez.
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            mesaj = response_data['candidates'][0]['content']['parts'][0]['text']
            return mesaj.strip()
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        return f"HATA: API İsteği Reddedildi ({e.code}). {error_msg}"
    except Exception as e:
        return f"HATA: {e}"
