import json
import urllib.request
import urllib.error
from .config import load_api_key

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
TIMEOUT_SECONDS = 30

def generate_commit_message(diff_text: str) -> str:
    api_key = load_api_key()
    
    if not api_key:
        return "ERROR: No API key found. Run 'oto-commit setup' or set the GEMINI_API_KEY environment variable."

    prompt = f"""
    You are a senior software engineer. Analyse the git diff below.
    Understand the real intent of the changes and write a single, clear, professional commit message in English
    that follows the Conventional Commits format (feat:, fix:, chore:, refactor:, docs:, ...).
    Return only the commit message, nothing else.
    
    {diff_text}
    """
    
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }).encode('utf-8')
    
    try:
        # The key travels in a header rather than the URL, so it never ends up in proxy/access logs.
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={'Content-Type': 'application/json', 'x-goog-api-key': api_key},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            message = response_data['candidates'][0]['content']['parts'][0]['text']
            return message.strip()
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        return f"ERROR: API request rejected ({e.code}). {error_msg}"
    except Exception as e:
        return f"ERROR: {e}"
