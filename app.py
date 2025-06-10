import streamlit as st
import pickle
from newspaper import Article
from urllib.parse import urlparse
from utils.news_utils import summarize_text
import nltk 
nltk.download('punkt_tab')


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
st.set_page_config(page_title="NewsVerifier", layout="centered")
st.title("📰 NewsVerifier: Real or Rubbish?")
st.markdown("Choose how you'd like to verify the news:")

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
        if st.session_state["prediction_result"] == 1:
            st.markdown("<h4 style='color: green;'>🟢 REAL News</h4>", unsafe_allow_html=True)

            if st.button("🔍 Summarize this article"):
                summary = summarize_text(st.session_state["user_text"], sentence_count=10)
                st.markdown("**📝 Summary:**")
                st.success(summary)
        else:
            st.markdown("<h4 style='color: red;'>🔴 FAKE News</h4>", unsafe_allow_html=True)

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

        if prediction == 1:
            st.markdown("<h4 style='color: green;'>🟢 REAL News</h4>", unsafe_allow_html=True)
            if st.button("🔍 Summarize this article"):
                summary = summarize_text(result['text'], sentence_count=3)
                st.markdown("**📝 Summary:**")
                st.success(summary)
        else:
            st.markdown("<h4 style='color: red;'>🔴 FAKE News</h4>", unsafe_allow_html=True)

