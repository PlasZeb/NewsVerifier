from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Opcionális: NLTK 'punkt' biztosítása, mert a Sumy tokenizálója NLTK-t használhat
def _ensure_nltk_punkt():
    try:
        import nltk
        # Ha nincs letöltve, megpróbáljuk
        nltk.data.find('tokenizers/punkt')
    except Exception:
        try:
            import nltk
            nltk.download('punkt')
        except Exception:
            pass

def summarize_text(text, sentence_count=3):
    try:
        if not text or len(text.split()) < 30:
            return "Text too short to summarize."

        # Biztosítjuk, hogy a szükséges NLTK erőforrások elérhetőek legyenek
        _ensure_nltk_punkt()

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        result = " ".join(str(sentence) for sentence in summary)
        if result.strip():
            return result

        # Ha a Sumy nem tudott összefoglalót készíteni, próbáljunk egyszerű mondat-vágást
        try:
            import nltk
            sentences = nltk.sent_tokenize(text)
            return " ".join(sentences[:sentence_count]) or "Summary could not be generated."
        except Exception:
            # Regex-alapú nagyon egyszerű fallback
            import re
            sentences = re.split(r"(?<=[.!?])\s+", text)
            return " ".join(sentences[:sentence_count]) or "Summary could not be generated."

    except Exception as e:
        # Pontosabb hibaüzenet az NLTK erőforrásokra
        msg = str(e)
        if 'punkt_tab' in msg or 'punkt' in msg:
            return "Summary generation error: NLTK 'punkt' tokenizer hiányzik. Futtasd: python -c \"import nltk; nltk.download('punkt')\""
        return f"Summary generation error: {msg}"



