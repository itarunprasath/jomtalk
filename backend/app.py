from flask import Flask, request, jsonify, render_template
from gtts import gTTS
from flask import send_file
from flask_cors import CORS
from utils.translation import translate_text
from utils.engtomalay import eng_to_malay_reply
#from utils.test import translate_text
from rapidfuzz import fuzz
import os
import sys
import io
import json
#--from utils.translation import translate_text

# --- Ensure Python can find your 'utils' module ---
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# --- Import your local utils ---
# try:
#     from utils.translation import translate_text
# except ImportError as e:
#     print("⚠️ Could not import translate_text:", e)
#     def translate_text(text): return text  # fallback

app = Flask(__name__, template_folder="templates")
CORS(app)

try:
    dict_path = os.path.join(os.path.dirname(__file__), "..", "models", "eng_to_malay.json")
    dict_path = os.path.abspath(dict_path)  # normalize path
    with open(dict_path, "r", encoding="utf-8") as f:
        eng_to_malay = json.load(f)
    print(f"✅ Loaded eng_to_malay.json from {dict_path}")
except Exception as e:
    print("⚠️ Could not load eng_to_malay.json:", e)
    eng_to_malay = {}  # fallback empty dict

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.json
    text = data.get("text", "")
    translated = translate_text(text)
    return jsonify({"input": text, "translated": translated})


@app.route("/api/reply", methods=["POST"])
def reply():
    """Convert English reply into Malay slang version using dictionary + AI fallback."""
    data = request.json
    text = data.get("text", "")

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    # Use hybrid translation
    malay_reply = eng_to_malay_reply(text)

    return jsonify({"input": text, "reply": malay_reply})

@app.route("/api/tts", methods=["POST"])
def tts():
    """Convert Malay text to speech using gTTS"""
    data = request.json
    text = data.get("text", "")

    if not text.strip():
        return jsonify({"error": "No text provided"}), 400

    try:
        # Generate speech in Malay
        tts = gTTS(text=text, lang="ms")  
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        return send_file(
            mp3_fp,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="output.mp3"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/coach", methods=["POST"])
def coach():
    """
    Compare user's spoken Malay text to the target phrase.
    Uses full-sentence fuzzy matching for more realistic scoring.
    """
    from rapidfuzz import fuzz
    import string

    data = request.json
    target = data.get("target", "").strip()
    user_input = data.get("user_input", "").strip()

    if not target or not user_input:
        return jsonify({"error": "Missing target or user_input"}), 400

    # --- Normalize text ---
    def normalize_text(text: str) -> str:
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = text.replace("-", " ")  # Treat hyphens as spaces
        return " ".join(text.split())

    target_norm = normalize_text(target)
    user_norm = normalize_text(user_input)

    # --- Calculate similarity ---
    score = fuzz.ratio(target_norm, user_norm)  # 0-100
    success = score >= 85

    return jsonify({
        "target": target,
        "user_input": user_input,
        "overall_score": int(score),
        "success": success,
        "message": "✅ Good pronunciation!" if success else "❌ Try again.",
    })

        
if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
