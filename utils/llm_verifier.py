"""
LLM-alapú hír ellenőrző modul
Használat: Google Gemini API-n keresztül ellenőrzi a hír hitelességét
"""

import os
from dotenv import load_dotenv

# Opcionális importok védetten, hogy az app ne omoljon össze, ha a csomag hiányzik
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except Exception:
    st = None
    STREAMLIT_AVAILABLE = False

# .env fájl betöltése
load_dotenv()

def verify_news_with_llm(news_text, api_key=None):
    """
    LLM-mel ellenőrzi a hír valóságtartalmát
    
    Args:
        news_text (str): A vizsgálandó hír szövege
        api_key (str): Gemini API kulcs (opcionális, környezeti változóból is olvasható)
    
    Returns:
        dict: Eredmény dictionary az alábbi kulcsokkal:
            - success (bool): Sikeres volt-e az ellenőrzés
            - prediction (str): "REAL", "FAKE", vagy "UNCERTAIN"
            - confidence (str): Az LLM bizonyossági szintje
            - reasoning (str): Az LLM indoklása
            - error (str): Hibaüzenet, ha volt hiba
    """
    try:
        # Ellenőrizzük, hogy a google-generativeai csomag elérhető-e
        if not GENAI_AVAILABLE:
            return {
                "success": False,
                "error": "A 'google-generativeai' csomag nincs telepítve. Telepítsd a környezetbe (pip install google-generativeai vagy add hozzá a requirements.txt-hez), majd indítsd újra az alkalmazást."
            }

        # API kulcs beállítása (robosztus keresés secrets/env)
        if api_key:
            genai.configure(api_key=api_key)
        else:
            def _clean_key(v: str):
                if not v:
                    return None
                v = v.strip()
                if len(v) >= 2 and ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                    v = v[1:-1].strip()
                return v or None

            def _find_key_from_secrets():
                if not STREAMLIT_AVAILABLE:
                    return None
                try:
                    for k in ["GEMINI_API_KEY", "gemini_api_key", "GEMINI", "GEMINI_KEY"]:
                        v = _clean_key(st.secrets.get(k, None))
                        if v:
                            return v
                except Exception:
                    return None
                return None

            def _find_key_from_env():
                for k in ["GEMINI_API_KEY", "gemini_api_key", "GEMINI", "GEMINI_KEY"]:
                    v = _clean_key(os.getenv(k))
                    if v:
                        return v
                return None

            api_key_found = _find_key_from_secrets() or _find_key_from_env()

            if not api_key_found:
                return {
                    "success": False,
                    "error": "Gemini API kulcs nincs beállítva. Állítsd be a GEMINI_API_KEY-t (Streamlit secrets vagy .env), vagy add meg az API kulcsot az alkalmazásban."
                }
            genai.configure(api_key=api_key_found)
        
        # LLM prompt összeállítása - CSAK 2 sor (PREDICTION + CONFIDENCE)
        prompt = f"""ANALYZE THIS NEWS QUICKLY AND ANSWER WITH TWO LINES ONLY:

NEWS:
{news_text[:5000]}

RESPOND WITH EXACTLY TWO LINES - NOTHING ELSE, NO EXPLANATION:
PREDICTION: REAL or FAKE or UNCERTAIN
CONFIDENCE: HIGH or MEDIUM or LOW"""

        # Gemini modell inicializálása (v1beta-hoz kompatibilis modell)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # API hívás - NO STREAMING, így nem csonkul
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Alacsonyabb érték konzisztensebb eredményhez
                max_output_tokens=1000,  # Bővebb limit az indoklásnak
                top_p=0.9,
                top_k=40
            ),
            stream=False  # Teljes válasz egy kérésben
        )
        
        # Debug: ellenőrizzük, hogy a válasz teljes-e
        finish_reason = response.candidates[0].finish_reason if response.candidates else None
        
        # Válasz feldolgozása: csak PREDICTION + CONFIDENCE sorokat várunk
        result_text = (response.text or "").strip()
        
        # Soronkénti feldolgozás
        lines = [line.strip() for line in result_text.split('\n') if line.strip()]
        
        pred = "UNCERTAIN"
        conf = "LOW"
        
        for line in lines:
            upper_line = line.upper()
            if upper_line.startswith("PREDICTION:"):
                pred_val = line.split(":", 1)[1].strip().upper()
                if pred_val in ["REAL", "FAKE", "UNCERTAIN"]:
                    pred = pred_val
            elif upper_line.startswith("CONFIDENCE:"):
                conf_val = line.split(":", 1)[1].strip().upper()
                if conf_val in ["HIGH", "MEDIUM", "LOW"]:
                    conf = conf_val
        
        # Indoklás: az LLM válasz többi sora vagy általános üzenet
        all_text = result_text.replace("PREDICTION:", "").replace("CONFIDENCE:", "").strip()
        # Csak az első 100 karakter az indoklás
        reas = all_text[:150] if all_text else f"Az LLM úgy értékelte: {pred} (Bizonyosság: {conf})"
        
        return {
            "success": True,
            "prediction": pred,
            "confidence": conf,
            "reasoning": reas,
            "error": None
        }


            
    except Exception as e:
        return {
            "success": False,
            "error": f"LLM ellenőrzési hiba: {str(e)}"
        }


def verify_news_with_llm_simple(news_text, api_key=None):
    """
    Egyszerűsített verzió, ami csak a predikciót adja vissza
    
    Returns:
        str: "REAL", "FAKE", "UNCERTAIN" vagy hibaüzenet
    """
    result = verify_news_with_llm(news_text, api_key)
    
    if result["success"]:
        return result["prediction"]
    else:
        return f"ERROR: {result['error']}"
