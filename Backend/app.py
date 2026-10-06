import os
import base64
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")

load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MURF_API_KEY = os.getenv("MURF_API_KEY", "").strip()

# Change this only if you want to use another model available to your Gemini API key.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

# Global auto-routes to the nearest Murf region. For India, the regional endpoint
# can be selected with MURF_BASE_URL=https://in.api.murf.ai
MURF_BASE_URL = os.getenv(
    "MURF_BASE_URL",
    "https://global.api.murf.ai"
).rstrip("/")

if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None

PROMPTS = {
    "Summary": """
You are a professional tourist guide.
Create a concise, engaging audio-guide script about "{place}" in {language}.

Cover:
- Historical significance
- Why the destination is famous
- Important architectural, cultural, or historical highlights
- One or two interesting facts

Write naturally for spoken narration. Avoid excessive dates and academic language.
Target roughly 150-220 words.
Respond ONLY in {language}.
""",
    "Detailed": """
You are a professional tourist guide.
Create an immersive audio-guide script about "{place}" in {language}.

Cover:
- Historical background and timeline
- Architectural design and unique features
- Cultural importance and notable events
- Interesting facts
- Useful visitor-oriented context

Write naturally as a spoken narration, with clear storytelling and no markdown.
Target roughly 300-450 words.
Respond ONLY in {language}.
"""
}

def error_response(message, status=500, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status

def generate_description(place, answer_type, language):
    if not gemini_client:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to the .env file and restart the server."
        )

    prompt = PROMPTS[answer_type].format(place=place, language=language)

    models_to_try = [
        GEMINI_MODEL,
        "gemini-3.1-flash-lite",
    ]

    last_error = None

    for model in models_to_try:
        for attempt in range(3):
            try:
                response = gemini_client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                text = (response.text or "").strip()

                if not text:
                    raise RuntimeError("Gemini returned an empty response.")

                return text

            except Exception as exc:
                last_error = exc
                error_text = str(exc)

                # Retry temporary Gemini availability/rate-limit errors.
                if any(code in error_text for code in ["429", "500", "503"]):
                    import time
                    time.sleep(2 ** attempt)
                    continue

                # Permanent error: don't keep retrying.
                raise

    raise RuntimeError(
        f"Gemini could not generate the guide after retries: {last_error}"
    )

def generate_speech(text, voice_id, locale):
    if not MURF_API_KEY:
        raise RuntimeError(
            "MURF_API_KEY is missing. Add it to the .env file and restart the server."
        )

    url = f"{MURF_BASE_URL}/v1/speech/stream"

    headers = {
    "api-key": MURF_API_KEY,
    "Content-Type": "application/json",
}

    payload = {
        "voiceId": voice_id,
        "text": text,
        "model": "falcon-2",
        "locale": locale,
        "format": "MP3",
        "sampleRate": 24000,
        "channelType": "MONO",
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=(30, 120),
        )

        if not response.ok:
            try:
                details = response.json()
            except Exception:
                details = response.text[:2000]

            raise RuntimeError(
                f"Murf API returned HTTP {response.status_code}: {details}"
            )

        audio_chunks = []

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                audio_chunks.append(chunk)

        audio_bytes = b"".join(audio_chunks)

        if not audio_bytes:
            raise RuntimeError("Murf returned an empty audio response.")    

        return audio_bytes

    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to Murf API: {exc}") from exc

@app.get("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.get("/index.js")
def javascript():
    return send_from_directory(FRONTEND_DIR, "index.js")


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "gemini_configured": bool(GEMINI_API_KEY),
        "murf_configured": bool(MURF_API_KEY),
        "gemini_model": GEMINI_MODEL,
        "murf_base_url": MURF_BASE_URL,
    })

@app.post("/generate-audio-guide")
def generate_audio_guide():
    try:
        data = request.get_json(silent=True) or {}

        place = str(data.get("place", "")).strip()
        answer_type = str(data.get("answerType", "Summary")).strip()
        language = str(data.get("language", "English")).strip()
        voice_id = str(data.get("voiceId", "")).strip()
        locale = str(data.get("locale", "")).strip()

        if not place:
            return error_response("Please select a destination.", 400)

        if answer_type not in PROMPTS:
            return error_response("Invalid guide length.", 400)

        if not voice_id or not locale:
            return error_response("Voice configuration is missing.", 400)

        description = generate_description(place, answer_type, language)
        audio_bytes = generate_speech(description, voice_id, locale)
        encoded_audio = base64.b64encode(audio_bytes).decode("utf-8")

        return jsonify({
            "description": description,
            "audioBase64": encoded_audio,
            "mimeType": "audio/mpeg",
        })

    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}")
        return error_response(
            "Could not generate the travel guide.",
            500,
            str(exc)
        )

if __name__ == "__main__":
    print("AI Travel Guide running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
