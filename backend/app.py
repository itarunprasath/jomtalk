from flask import Flask, request, jsonify, render_template
from gtts import gTTS
from flask import send_file
from flask_cors import CORS
import os
import io
import json
from utils.translation import translate_text

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
    """Convert English reply into Malay slang version."""
    data = request.json
    text = data.get("text", "")
    words = text.split()
    converted = []
    for w in words:
        lw = w.lower()
        if lw in eng_to_malay:
            converted.append(eng_to_malay[lw])
        else:
            converted.append(w)
    return jsonify({"input": text, "reply": " ".join(converted)})
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
        
if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
