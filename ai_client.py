import os
import requests
from typing import Dict
from dotenv import load_dotenv, find_dotenv

# Load .env if present
load_dotenv(find_dotenv())

# --- Configuration (Based on your input) ---
# Default official endpoint for generateContent
GEMINI_API_URL = os.getenv("GEMINI_API_URL") or \
                 "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Helper Function for Parsing (Kept from your first snippet) ---
def _extract_text_from_generate_content(resp_json: Dict) -> str:
    """Extract readable text from a standard generateContent-style response."""
    try:
        # Attempts to extract text from the standard Google response structure
        candidates = resp_json.get("candidates")
        if candidates and isinstance(candidates, list) and len(candidates) > 0:
            first_candidate = candidates[0]
            # Handle standard 'text' field directly
            if 'text' in first_candidate:
                return first_candidate['text']
            # Fallback for structured content
            content = first_candidate.get("content")
            if isinstance(content, dict) and content.get("parts"):
                for part in content["parts"]:
                    if "text" in part:
                        return part["text"]
    except Exception:
        pass
    
    # Fallback: return JSON string representation
    return str(resp_json)


# --- Corrected API Call Function ---
def call_gemini(prompt: str) -> Dict:
    """Call the official Google Generative Language generateContent endpoint."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY must be set in environment variables.")

    # 1. Use the full, nested payload required by the generateContent API
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    # 2. Add API key as a query parameter to the URL for standard authentication
    request_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
    
    # Headers only need to specify content type
    headers = {"Content-Type": "application/json"}

    print(f"Calling URL: {request_url}") 
    
    resp = requests.post(request_url, json=payload, headers=headers, timeout=30)
    
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error: {resp.status_code} {resp.text}")

    resp_json = resp.json()
    
    # 3. Use the correct parsing logic
    text = _extract_text_from_generate_content(resp_json)
    
    return {"raw": resp_json, "text": text}
