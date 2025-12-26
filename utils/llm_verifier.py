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
        
        # LLM prompt összeállítása (kizárólag JSON választ kérünk)
        prompt = f"""Elemezd az alábbi hírcikket és döntsd el, hogy valós vagy álhír-e.

HÍRCIKK:
{news_text[:8000]}  # Gemini nagyobb kontextust támogat

Elemzési szempontok:
1. A cikk nyelvezete objektív vagy túlzottan érzelmes/szenzációhajhász?
2. Vannak-e konkrét hivatkozások, források vagy csak állítások?
3. A tények ellenőrizhetőek és logikusak?
4. Az írás professzionális vagy amatőr?
5. Vannak-e ellentmondások vagy valószínűtlen állítások?

Válaszolj JSON formátumban az alábbi formában, kizárólag a JSON-t add vissza (lehetőleg ```json kódblokkban), extra szöveg nélkül:
{{
    "prediction": "REAL" vagy "FAKE" vagy "UNCERTAIN",
    "confidence": "HIGH" vagy "MEDIUM" vagy "LOW",
    "reasoning": "Rövid indoklás magyarul (max 2-3 mondat)"
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
        
        # Válasz feldolgozása és JSON kinyerése robusztusan
        result_text = (response.text or "").strip()
        import json
        
        def extract_json(text: str):
            # codeblock JSON
            if "```json" in text:
                try:
                    return text.split("```json", 1)[1].split("```", 1)[0].strip()
                except Exception:
                    pass
            # bármilyen codeblock
            if "```" in text:
                try:
                    return text.split("```", 1)[1].split("```", 1)[0].strip()
                except Exception:
                    pass
            # kiegyensúlyozott kapcsos zárójelek keresése
            start = -1
            depth = 0
            for i, ch in enumerate(text):
                if ch == '{':
                    if depth == 0:
                        start = i
                    depth += 1
                elif ch == '}':
                    if depth > 0:
                        depth -= 1
                        if depth == 0 and start != -1:
                            return text[start:i+1].strip()
            return None
        
        json_candidate = extract_json(result_text)
        if json_candidate:
            try:
                result_json = json.loads(json_candidate)
                pred = (result_json.get("prediction") or "UNCERTAIN").upper()
                conf = (result_json.get("confidence") or "LOW").upper()
                reas = result_json.get("reasoning")
                # Ha üres vagy JSON-szerű, adjunk barátságos alapértelmezést
                if not isinstance(reas, str) or not reas.strip() or reas.strip().startswith("{"):
                    outside = result_text.replace(json_candidate, "").strip()
                    if outside:
                        reas = outside
                    else:
                        reas = f"Az LLM nem adott külön indoklást. Eredmény: {pred}, Bizonyosság: {conf}."
                return {
                    "success": True,
                    "prediction": pred if pred in ["REAL", "FAKE", "UNCERTAIN"] else "UNCERTAIN",
                    "confidence": conf if conf in ["HIGH", "MEDIUM", "LOW"] else "LOW",
                    "reasoning": reas,
                    "error": None
                }
            except Exception:
                pass
        # Ha minden kudarcot vall, adjunk vissza nyers választ indoklásként
        return {
            "success": True,
            "prediction": "UNCERTAIN",
            "confidence": "LOW",
            "reasoning": result_text or "Nincs indoklás.",
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
