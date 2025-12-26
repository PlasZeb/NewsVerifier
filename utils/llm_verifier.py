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
        
        # LLM prompt összeállítása
        prompt = f"""Elemezd az alábbi hírcikket és döntsd el, hogy valós vagy álhír-e.

HÍRCIKK:
{news_text[:8000]}  # Gemini nagyobb kontextust támogat

Elemzési szempontok:
1. A cikk nyelvezete objektív vagy túlzottan érzelmes/szenzációhajhász?
2. Vannak-e konkrét hivatkozások, források vagy csak állítások?
3. A tények ellenőrizhetőek és logikusak?
4. Az írás professzionális vagy amatőr?
5. Vannak-e ellentmondások vagy valószínűtlen állítások?

Válaszolj JSON formátumban az alábbi formában:
{{
    "prediction": "REAL" vagy "FAKE" vagy "UNCERTAIN",
    "confidence": "HIGH" vagy "MEDIUM" vagy "LOW",
    "reasoning": "Short explanation of the AI analysis (max 2-3 sentences)"
}}"""

        # Gemini modell inicializálása (v1beta-hoz kompatibilis modell)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # API hívás
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Alacsonyabb érték konzisztensebb eredményhez
                max_output_tokens=500
            )
        )
        
        # Válasz feldolgozása
        result_text = response.text.strip()
        
        # JSON válasz parse-olása
        import json
        try:
            # Ha a válasz JSON kód blokkban van, tisztítjuk
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result_json = json.loads(result_text)
            
            return {
                "success": True,
                "prediction": result_json.get("prediction", "UNCERTAIN"),
                "confidence": result_json.get("confidence", "LOW"),
                "reasoning": result_json.get("reasoning", "Nincs indoklás."),
                "error": None
            }
        except json.JSONDecodeError:
            # Ha nem sikerült JSON-ként parse-olni, visszaadjuk a nyers szöveget
            return {
                "success": True,
                "prediction": "UNCERTAIN",
                "confidence": "LOW",
                "reasoning": result_text,
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
