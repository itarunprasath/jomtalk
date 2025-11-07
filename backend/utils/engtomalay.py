import os
import json
import re
from transformers import pipeline

# Load English → Malay dictionary
dict_path = os.path.join(os.path.dirname(__file__), "../../models/eng_to_malay.json")
with open(dict_path, "r", encoding="utf-8") as f:
    eng_to_malay = json.load(f)

# AI translator for unknown words
eng2malay_translator = pipeline(
    "translation",
    model="facebook/nllb-200-distilled-600M",
    src_lang="eng_Latn",
    tgt_lang="zsm_Latn"
)

PROTECTED_TERMS = ["nasi lemak", "teh tarik", "roti canai", "mee goreng", "satay"]

def eng_to_malay_reply(text: str) -> str:
    words = text.split()
    converted = []

    for w in words:
        lw = w.lower()
        if lw in eng_to_malay:
            converted.append(eng_to_malay[lw])
        else:
            converted.append(w)

    if all(w.lower() in eng_to_malay for w in words):
        return " ".join(converted)

    protected_text = " ".join(converted)
    try:
        ai_translation = eng2malay_translator(protected_text)[0]['translation_text']
        for term in PROTECTED_TERMS:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            ai_translation = pattern.sub(term, ai_translation)
        return ai_translation
    except Exception as e:
        return " ".join(converted) + f" ⚠️ AI translation failed: {str(e)}"
