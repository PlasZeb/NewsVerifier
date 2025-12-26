from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Opcionális: NLTK 'punkt' biztosítása, mert a Sumy tokenizálója NLTK-t használhat
def _ensure_nltk_punkt():
    try:
        import os
        import nltk
        # Állítsuk be a data path-ot Cloud kompatibilis helyre
        data_dir = os.environ.get('NLTK_DATA', '/tmp/nltk_data')
        os.makedirs(data_dir, exist_ok=True)
        if data_dir not in nltk.data.path:
            nltk.data.path.append(data_dir)
        # Ha nincs letöltve, megpróbáljuk
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True, download_dir=data_dir)
    except Exception:
        # Ha semmi nem sikerül, hagyjuk, majd regex fallback működni fog
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
        # Hiba esetén próbáljunk regex alapú fallback-ot, hogy ne álljon le
        try:
            import re
            sentences = re.split(r"(?<=[.!?])\s+", text or "")
            if sentences:
                return " ".join(sentences[:sentence_count])
        except Exception:
            pass
        # Végső barátságos hibaüzenet
        return "Summary could not be generated due to missing tokenizers."



