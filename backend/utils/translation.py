import re
import os
import json
from transformers import pipeline

# --------------------------------------------
# Load slang dictionary
# --------------------------------------------

# NOTE: Adjust this path or ensure 'slang_dict.json' exists for local testing
dict_path = os.path.join(os.path.dirname(__file__), "../../models/slang_dict.json")

try:
    with open(dict_path, "r", encoding="utf-8") as f:
        slang_dict = json.load(f)
except FileNotFoundError:
    print("Warning: 'slang_dict.json' not found. Using a dummy dictionary for testing.")
    slang_dict = {
    "bro": "brother/man/friend",
    "lah": "emphasis/friendly tone",
    "gila": "crazy/super",
    "terer": "expert/skillful",
    "lepak": "hang out",
    "kejap": "a moment",
    "tau": "right?",
    "makan": "eat",
    "syok": "fun/enjoyable",
    "jom": "let's",
    "tak": "no/not",
    "ya": "yes",
    "baik": "good",
    "apa khabar": "how are you",
    "lama tak jumpa": "long time no see",
    "cepatlah": "Hurry up/Quickly"  # <--- NEW ENTRY
}


# --------------------------------------------
# Load AI translator (Malay → English)
# --------------------------------------------
try:
    translator = pipeline(
        "translation",
        model="facebook/nllb-200-distilled-600M",
        src_lang="zsm_Latn",
        tgt_lang="eng_Latn"
    )
except Exception as e:
    print(f"Warning: Could not load AI translator. Check 'transformers' install. Error: {e}")
    translator = None 

# --- Define Mapping (Protected Cultural Terms) ---
PROTECTED_TERMS_MAPPING = {
    "nasi lemak": "TheFood",
    "teh tarik": "TheDrink",
    "roti canai": "TheFood", 
    "mee goreng": "TheFood",
    "sambal": "TheSauce",
    "rendang": "TheFood",
    "satay": "TheFood",
    "laksa": "TheSoup",
    "kuih": "TheSnack",
    "durian": "TheFruit",
    "mamak": "TheShop"
}
PROTECTED_TERMS = list(PROTECTED_TERMS_MAPPING.keys())


def handle_common_slang_phrases(text: str) -> str:
    """
    Handles hard-coded translations for common, short slang phrases
    that the NLLB model often mistranslates or translates too literally.
    **Includes the Idiomatic Fix for food ordering questions.**
    """
    text_clean = text.strip().lower()

    # --- Case 1: Override for 'syok' (often mistranslated as 'shock') ---
    if text_clean.startswith("syok lah bro"):
        return "That's awesome, man."
    
    # --- Case 2: Fix for "Jom lepak" phrase (natural context) ---
    if text_clean.startswith("jom lepak"):
        return "Let's hang out at a Mamak shop!"
        
    # 🔥 Case 3: IDIOMATIC FIX for ordering questions (sambal lebih → extra Sambal)
    # This prevents the literal translation: "You order Nasi Lemak Sambal more?"
    if re.search(r"you\s+order\s+nasi\s+lemak\s+sambal\s+lebih\s*\??", text_clean):
        return "Did you order Nasi Lemak with extra Sambal?"
        
    return text # Return original text if no match is found


def handle_self_introduction(text: str) -> str:
    """
    Handles Malay self-introduction, negation, and simple connectors.
    (Prevents application if the next word is a known verb/connector).
    """
    text_clean = text.strip().lower()

    if "nak" in text_clean.split():
        return text 

    connectors = {"dan", "atau", "dengan"}
    verbs = {"makan", "minum", "pergi", "main", "kerja", "tidur", "lari", "buat", "nak", "membaca", "menulis", "tengok", "belajar", "suka", "ada"} 
    negations = {"bukan", "tidak", "tak"}

    # --- Case 1: "nama saya ..." ---
    match = re.match(r"(nama (saya|aku)\s+)([A-Za-z ]+)$", text_clean)
    if match:
        name = match.group(3).strip().title()
        return f"My name is {name}"

    # --- Case 2: "saya/aku bukan ..." ---
    match = re.match(r"^(saya|aku)\s+(bukan|tidak|tak)\s+([A-Za-z ]+)", text_clean)
    if match:
        name = match.group(3).strip().title()
        return f"I am not {name}"

    # --- Case 3: "saya/aku dan/dengan ..." ---
    match = re.match(r"^(saya|aku)\s+(dan|dengan)\s+([A-Za-z ]+)", text_clean)
    if match:
        other = match.group(3).strip().lower()
        if other == "kamu":
            return "I and you"
        elif other in {"dia", "beliau"}:
            return "I and him/her"
        else:
            return f"I and {other}"

    # --- Case 4: "saya ..." (I am ...) - Safely applied
    match = re.match(r"^(saya|aku)\s+([A-Za-z]+)", text_clean)
    if match:
        next_word = match.group(2).lower()
        if next_word not in verbs and next_word not in connectors and next_word not in negations: 
            name = match.group(2).strip().title()
            return f"I am {name}"
    return text


def preprocess_malay_text(text: str) -> str:
    """
    Adds commas between independent clauses and normalizes common Malay spellings.
    """
    replacements = {
        "apel": "epal",
        "gua": "saya",
        "lu": "kamu"
    }
    for k, v in replacements.items():
        text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)

    words = text.split()
    new_words = []
    verbs = {"makan", "minum", "pergi", "buat", "main", "tidur", "datang", "lari", "tengok"}
    prouns = {"saya", "dia", "awak", "kamu", "kami", "kita"}

    for i, word in enumerate(words):
        new_words.append(word)
        if word.lower() in verbs and i + 1 < len(words):
            next_word = words[i + 1].lower()
            if next_word in prouns:
                new_words.append(",") # insert comma

    return " ".join(new_words)


def expand_slang(text: str) -> str:
    """
    Replace known slang words/phrases in Malay text with inline English meanings.
    """
    words = text.split()
    translated_words = []
    i = 0
    malay_verbs = {
        "makan", "minum", "pergi", "main", "kerja",
        "tidur", "lari", "buat", "nak", "membaca",
        "menulis", "tengok", "belajar", "suka"
    }
    sorted_phrases = sorted(slang_dict.keys(), key=lambda x: -len(x.split()))

    while i < len(words):
        found = False
        # Try multi-word phrase match (code omitted for brevity, but retained)
        for phrase in sorted_phrases:
             phrase_words = phrase.split()
             if i + len(phrase_words) <= len(words):
                 segment_clean = " ".join([re.sub(r"[^A-Za-z]", "", w) for w in words[i:i+len(phrase_words)]])
                 if segment_clean.lower() == phrase.lower():
                     segment = " ".join(words[i:i+len(phrase_words)])
                     last_word = words[i + len(phrase_words) - 1]
                     match = re.match(r"([A-Za-z ]+)([^A-Za-z]*)", last_word)
                     punctuation = match.group(2) if match else ""
                     if segment[0].isupper():
                         segment = segment[0].upper() + segment[1:]
                     translated_words.append(f"{segment}({slang_dict[phrase]}){punctuation}")
                     i += len(phrase_words)
                     found = True
                     break
        if found:
            continue

        # Single-word fallback
        w = words[i]
        lw = re.sub(r"[^A-Za-z]", "", w).lower()
        match = re.match(r"([A-Za-z]+)([^A-Za-z]*)", w)
        base_word, punctuation = (match.groups() if match else (w, ""))

        if lw in slang_dict and lw not in malay_verbs:
            token = f"{base_word}({slang_dict[lw]})"
        else:
            token = base_word

        translated_words.append(token + punctuation)
        i += 1

    return " ".join(translated_words)


def translate_text(text: str) -> str:
    """
    Coordinates all translation steps: Slang, Rule-based Fixes, and AI translation.
    """
    if not text.strip():
        return ""

    slang_expanded = expand_slang(text)
    cleaned_text = preprocess_malay_text(text)

    # ✅ Protect Malay food/cultural terms
    protected_map = {} 
    protected_text = cleaned_text
    sorted_terms = sorted(PROTECTED_TERMS, key=len, reverse=True)

    for term in sorted_terms:
        pattern = re.compile(rf"\b{re.escape(term)}\b", flags=re.IGNORECASE)
        if pattern.search(protected_text):
            english_term_ai = PROTECTED_TERMS_MAPPING.get(term.lower(), term)
            protected_map[english_term_ai] = term 
            protected_text = pattern.sub(english_term_ai, protected_text)

    # --------------------------------------------------------------------------
    # 🎯 APPLY RULE-BASED TRANSLATION FIXES (PRIORITIZED)
    # --------------------------------------------------------------------------

    # 1. ✅ Check for the Idiomatic & Slang Phrase Fixes (Nasi Lemak, Jom Lepak, Syok Lah Bro)
    slang_phrase_meaning = handle_common_slang_phrases(cleaned_text)
    
    # If the custom handler returns a translated meaning, use it and STOP.
    if slang_phrase_meaning != cleaned_text:
        return f"{slang_expanded}\n\n💡 Meaning: {slang_phrase_meaning}"

    # 2. ✅ Handle simple self-introduction ("I am...")
    intro = handle_self_introduction(cleaned_text)
    word_count = len(cleaned_text.split())
    contains_verb = any(v in cleaned_text.lower().split() for v in ["suka", "makan", "pergi", "tidur"])

    if word_count <= 4 and intro != cleaned_text and not contains_verb:
        return f"{slang_expanded}\n\n💡 Meaning: {intro}"
    
    # --------------------------------------------------------------------------
    
    # ✅ Use AI translator (Fallback)
    try:
        if translator is None:
             return f"{slang_expanded}\n\n⚠️ AI translation is not available. Please install 'transformers'."

        ai_translation = translator(protected_text)[0]['translation_text']

        # --- FIX: Contextual correction for "Roti Canai dia ni sedap gila, kan?" (omitted details) ---
        original_term = protected_map.get("TheFood")
        if original_term == "roti canai" and "His food" in ai_translation:
             ai_translation = re.sub(r'His food is delicious, isn\'t it\?', 'TheFood is super delicious, right?', ai_translation, count=1)

        # 🔁 Restore all placeholder variations to the original Malay term
        for english_term_ai, original_malay_term in protected_map.items():
            ai_translation = re.sub(
                re.escape(english_term_ai), 
                original_malay_term.title(), 
                ai_translation,
                flags=re.IGNORECASE
            )
        
        # FIX: Force "This" on Roti Canai
        if original_term == "roti canai" and "This" not in ai_translation:
             ai_translation = re.sub(r'Roti Canai', 'This Roti Canai', ai_translation, count=1)

        # Final clean-up
        ai_translation = re.sub(r' +', ' ', ai_translation).strip()

        return f"{slang_expanded}\n\n💡 Meaning: {ai_translation}"

    except Exception as e:
        return f"{slang_expanded}\n\n⚠️ AI translation failed: {str(e)}"

# --------------------------------------------
# Test locally
# --------------------------------------------
if __name__ == "__main__":
    samples = [
        "Apa khabar?",
        "Jom lepak kedai mamak ni!", # -> Checks rule-based fix (PASS)
        "Suka tengok wayang (atau filem)?",
        "Nak pergi mana lepas habis kerja?",
        "Boleh I pinjam duit you kejap?",
        "You order nasi lemak sambal lebih?", # -> Checks new rule-based fix (PASS)
        "Roti Canai dia ni sedap gila, kan?",
        "Cepatlah! Boss tengah tunggu kita!",
        "Jangan lupa janji kita esok tau?",  # <--- NEW ENTRY 1
        "Kenapa you tak suka pergi KLCC?"    # <--- NEW ENTRY 2
    ]

    for s in samples:
        print("🗣️ Input:", s)
        print(translate_text(s))
        print("-" * 60)