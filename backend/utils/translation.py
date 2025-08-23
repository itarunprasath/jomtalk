import re
import os
import json

dict_path = os.path.join(os.path.dirname(__file__), "../../models/slang_dict.json")
with open(dict_path, "r", encoding="utf-8") as f:
    slang_dict = json.load(f)

def translate_text(text: str) -> str:
    """Translate Malay slang words into English for easier understanding,
    even when multiple slang words are merged together (e.g. 'makanlah').
    Preserves capitalization and punctuation."""
    words = text.split()
    translated_words = []

    for w in words:
        # Separate punctuation from the word
        match = re.match(r"([A-Za-z]+)([^A-Za-z]*)", w)
        if match:
            base_word, punctuation = match.groups()
        else:
            base_word, punctuation = w, ""

        lw = base_word.lower()
        i = 0
        parts = []
        first = True
        while i < len(lw):
            found = False
            for key, meaning in slang_dict.items():
                if lw.startswith(key, i):
                    token = f"{key}({meaning})"
                    # Capitalize if original started uppercase & it's the first match
                    if first and base_word[0].isupper():
                        token = token[0].upper() + token[1:]
                    parts.append(token)
                    i += len(key)
                    found = True
                    first = False
                    break
            if not found:
                # If no slang match, just keep the character
                parts.append(lw[i])
                i += 1
                first = False

        # Join matched parts + reattach punctuation
        translated_words.append(" ".join(parts) + punctuation)

    return " ".join(translated_words)
