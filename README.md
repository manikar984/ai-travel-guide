# AI Travel Guide — Gemini + Murf AI

This package runs the supplied Travel Guide project with:
- Gemini for destination-guide text generation
- Murf Falcon 2 for text-to-speech
- Python + Flask backend
- HTML/CSS/JavaScript frontend

## 1. Requirements

Install:
- Python 3.10 or newer
- Internet connection
- A Gemini API key
- A Murf API key

## 2. Configure API keys

Copy `.env.example` to `.env`.

Then edit `.env`:

GEMINI_API_KEY=your_real_gemini_key
MURF_API_KEY=your_real_murf_key

Do NOT put API keys inside `Frontend/index.js` or upload `.env` to GitHub.

## 3. Windows

Double-click `run_windows.bat`.

The first run creates `.venv`, installs dependencies, and creates `.env`.
After adding the keys, run `run_windows.bat` again.

Open:
http://127.0.0.1:5000

## 4. Manual start

From this folder:

python -m venv .venv

Windows:
.venv\Scripts\activate

Then:
pip install -r requirements.txt
python Backend\app.py

Open:
http://127.0.0.1:5000

## 5. Test the server

Open:
https://ai-travel-guide-xmd5.onrender.com/

The response shows whether Gemini and Murf keys are configured.

## 6. How the application works

1. Select a destination.
2. Choose Summary or Detailed.
3. Choose language and voice gender.
4. Browser sends a POST request to `/generate-audio-guide`.
5. Flask asks Gemini for the travel narration.
6. Flask sends that narration to Murf Falcon 2.
7. Flask Base64-encodes the returned MP3.
8. Browser displays the transcript and audio player.

## 7. Important API note

The original project used Murf model `FALCON`. The current Murf streaming API uses `falcon-2`; this package has been updated accordingly.

## 8. If Murf returns a voice error

Voice names/IDs can change. Murf's API supports retrieving available voices from its voices endpoint. If one of the workshop voice names is unavailable on your account, update the `VOICES` mapping in `Frontend/index.js` with a voice supported by your Murf account.

## 9. Security

Never:
- commit `.env`
- paste API keys into frontend JavaScript
- put API keys directly into HTML
- publish your API keys in a GitHub repository

The backend is responsible for calling Gemini and Murf so the browser never receives your API keys.
