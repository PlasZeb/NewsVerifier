from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

def summarize_text(text, sentence_count=3):
    try:
        if not text or len(text.split()) < 30:
            return "Text too short to summarize."
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary = summarizer(parser.document, sentence_count)
        return " ".join(str(sentence) for sentence in summary) or "Summary could not be generated."
    except Exception as e:
        return f"Summary generation error: {str(e)}"



