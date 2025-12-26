import streamlit as st
import pickle
from newspaper import Article
from urllib.parse import urlparse
from utils.news_utils import summarize_text
from utils.llm_verifier import verify_news_with_llm
import nltk
from dotenv import load_dotenv
import os

# .env fájl betöltése
load_dotenv()

# NLTK tokenizáló letöltése és path beállítása
NLTK_DIR = "/tmp/nltk_data"
os.makedirs(NLTK_DIR, exist_ok=True)
try:
    nltk.data.path.append(NLTK_DIR)
    nltk.download('punkt', quiet=True, download_dir=NLTK_DIR)
except Exception:
    pass

# Streamlit konfiguráció
st.set_page_config(page_title="NewsVerifier", layout="wide")

# Force refresh
st.set_option('client.toolbarMode', 'viewer')

# Load the model and vectorizer
model = pickle.load(open("model/fake_news_model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

# Utility Functions
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def extract_news_from_url(url):
    if not is_valid_url(url):
        return {"error": "Invalid URL"}
    try:
        article = Article(url)
        article.download()
        article.parse()
        if not article.text.strip():
            return {"error": "Failed to retrieve news from the URL"}
        return {
            "title": article.title or "No Title",
            "author": article.authors or ["Unknown"],
            "publish_date": article.publish_date,
            "text": article.text.strip()
        }
    except Exception:
        return {"error": "Failed to retrieve news from the URL"}

def predict_news(text):
    text_vector = vectorizer.transform([text])
    prediction = model.predict(text_vector)[0]
    return prediction

# Streamlit UI
st.title("📰 NewsVerifier: Real or Rubbish?")
st.markdown("Choose how you'd like to verify the news:")

# DEBUG: Ellenőrzés
st.warning("🔄 **APPLIKÁCIÓ FRISSÍTVE** - v2.3 - MŰKÖDIK!")

# Inicializálás session_state-ben
if "use_llm" not in st.session_state:
    st.session_state["use_llm"] = False
if "gemini_api_key" not in st.session_state:
    st.session_state["gemini_api_key"] = None

# LLM beállítások - EGYSZERŰ SZEKCIÓ
st.markdown("## 🤖 Google Gemini AI Beállítás")
st.session_state["use_llm"] = st.checkbox("✅ Google Gemini AI aktiválása a hír-ellenőrzéshez", value=st.session_state["use_llm"])

if st.session_state["use_llm"]:
    st.info("""
    ✨ **Google Gemini AI ellenőrzés aktiválva!**
    
    - Részletes AI elemzés minden cikkhez
    - Indoklás és bizonyossági szint
    - Ingyenes API: https://aistudio.google.com/app/apikey
    """)
    
    # Kulcsforrás felderítése: secrets -> env -> manuális
    # Kulcs keresése több névváltozattal
    def _clean_key(v: str):
        if not v:
            return None
        # Levágjuk a whitespace-et és a környező idézőjeleket, ha vannak
        v = v.strip()
        if len(v) >= 2 and ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
            v = v[1:-1].strip()
        return v or None

    def _find_key_from_env():
        for k in ["GEMINI_API_KEY", "gemini_api_key", "GEMINI", "GEMINI_KEY"]:
            v = _clean_key(os.getenv(k))
            if v:
                return v
        return None

    def _find_key_from_secrets():
        try:
            for k in ["GEMINI_API_KEY", "gemini_api_key", "GEMINI", "GEMINI_KEY"]:
                v = _clean_key(st.secrets.get(k, None))
                if v:
                    return v
        except Exception:
            return None
        return None

    secret_key_value = _find_key_from_secrets()
    env_key_value = _find_key_from_env()

    auto_key_value = secret_key_value or env_key_value
    has_auto_key = bool(auto_key_value)

    if has_auto_key:
        st.success("✅ API kulcs automatikusan betöltve (környezet vagy Streamlit Secrets)!")
        
        # Automatikus kulcsot használjuk session-ben
        st.session_state["gemini_api_key"] = auto_key_value

        # Diagnostics - honnan jön a kulcs
        with st.expander("🔍 Diagnosztika: API kulcs forrása"):
            if secret_key_value:
                st.info("📦 Kulcs forrása: **Streamlit Secrets** (GEMINI_API_KEY)")
            elif env_key_value:
                st.info("🌍 Kulcs forrása: **Környezeti változó** (.env vagy rendszer)")
            st.caption("Ha Cloud-on futtat, a Streamlit Secrets az ajánlott módszer.")
    else:
        st.warning("Adj meg egy Gemini API kulcsot:")
        api_key = st.text_input("🔑 Gemini API Kulcs:", type="password", 
                               placeholder="sk-xxxxxxxxxxxx")
        if api_key:
            st.session_state["gemini_api_key"] = api_key
            st.success("✅ API kulcs elfogadva!")
            st.info("🔑 Kulcs forrása: **Manuális bemenet** (session)")

st.divider()

option = st.radio("Select Verification Mode", ["Verify by Input", "Verify by URL"])

if option == "Verify by Input":
    if "user_text" not in st.session_state:
        st.session_state["user_text"] = ""
    if "prediction_result" not in st.session_state:
        st.session_state["prediction_result"] = None

    st.session_state["user_text"] = st.text_area("📝 Paste the news content here:", value=st.session_state["user_text"], height=200)

    if st.button("Verify"):
        if len(st.session_state["user_text"].strip()) < 50:
            st.warning("⚠️ Please enter meaningful content (at least 50 characters).")
            st.session_state["prediction_result"] = None
        else:
            st.session_state["prediction_result"] = predict_news(st.session_state["user_text"])

    if st.session_state["prediction_result"] is not None:
        st.markdown("### 🎯 ML Model Eredmény:")
        if st.session_state["prediction_result"] == 1:
            st.markdown("<h4 style='color: green;'>🟢 REAL News</h4>", unsafe_allow_html=True)

            if st.button("🔍 Summarize this article"):
                summary = summarize_text(st.session_state["user_text"], sentence_count=10)
                st.markdown("**📝 Summary:**")
                st.success(summary)
        else:
            st.markdown("<h4 style='color: red;'>🔴 FAKE News</h4>", unsafe_allow_html=True)
        
        # LLM ellenőrzés hozzáadása
        if st.session_state["use_llm"]:
            st.markdown("---")
            st.markdown("### 🤖 LLM Alapú Elemzés:")
            with st.spinner("Gemini elemzi a hírt..."):
                llm_api_key = st.session_state.get("gemini_api_key", None)
                llm_result = verify_news_with_llm(st.session_state["user_text"], api_key=llm_api_key)
                
                if llm_result["success"]:
                    prediction = llm_result["prediction"]
                    confidence = llm_result["confidence"]
                    reasoning = llm_result["reasoning"]
                    
                    if prediction == "REAL":
                        st.markdown(f"<h4 style='color: green;'>🟢 REAL News (Bizonyosság: {confidence})</h4>", unsafe_allow_html=True)
                    elif prediction == "FAKE":
                        st.markdown(f"<h4 style='color: red;'>🔴 FAKE News (Bizonyosság: {confidence})</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h4 style='color: orange;'>🟡 BIZONYTALAN (Bizonyosság: {confidence})</h4>", unsafe_allow_html=True)
                    
                    st.markdown("**📊 LLM Indoklás:**")
                    st.info(reasoning)
                else:
                    st.error(f"❌ {llm_result['error']}")

elif option == "Verify by URL":
    user_url = st.text_input("🌐 Enter the news article URL:")

    if st.button("Fetch and Verify"):
        result = extract_news_from_url(user_url)
        if "error" in result:
            st.error(f"❌ {result['error']}")
        else:
            st.session_state["url_result"] = result
            st.session_state["url_prediction"] = predict_news(result["text"])
            st.session_state["url_verified"] = True

    if st.session_state.get("url_verified"):
        result = st.session_state["url_result"]
        prediction = st.session_state["url_prediction"]

        st.markdown(f"**Title:** {result['title']}")
        st.markdown(f"**Author(s):** {', '.join(result['author'])}")
        st.markdown(f"**Published on:** {result['publish_date']}")
        st.text_area("📄 Article Content:", value=result['text'][:10000], height=300)

        st.markdown("### 🎯 ML Model Eredmény:")
        if prediction == 1:
            st.markdown("<h4 style='color: green;'>🟢 REAL News</h4>", unsafe_allow_html=True)
            if st.button("🔍 Summarize this article"):
                summary = summarize_text(result['text'], sentence_count=3)
                st.markdown("**📝 Summary:**")
                st.success(summary)
        else:
            st.markdown("<h4 style='color: red;'>🔴 FAKE News</h4>", unsafe_allow_html=True)
        
        # LLM ellenőrzés hozzáadása
        if st.session_state["use_llm"]:
            st.markdown("---")
            st.markdown("### 🤖 LLM Alapú Elemzés:")
            with st.spinner("Gemini elemzi a hírt..."):
                llm_api_key = st.session_state.get("gemini_api_key", None)
                llm_result = verify_news_with_llm(result['text'], api_key=llm_api_key)
                
                if llm_result["success"]:
                    prediction_llm = llm_result["prediction"]
                    confidence = llm_result["confidence"]
                    reasoning = llm_result["reasoning"]
                    
                    if prediction_llm == "REAL":
                        st.markdown(f"<h4 style='color: green;'>🟢 REAL News (Bizonyosság: {confidence})</h4>", unsafe_allow_html=True)
                    elif prediction_llm == "FAKE":
                        st.markdown(f"<h4 style='color: red;'>🔴 FAKE News (Bizonyosság: {confidence})</h4>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<h4 style='color: orange;'>🟡 BIZONYTALAN (Bizonyosság: {confidence})</h4>", unsafe_allow_html=True)
                    
                    st.markdown("**📊 LLM Indoklás:**")
                    st.info(reasoning)
                else:
                    st.error(f"❌ {llm_result['error']}")

