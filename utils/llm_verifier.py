"""
LLM-alapú hír ellenőrző modul
Használat: Google Gemini API-n keresztül ellenőrzi a hír hitelességét
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

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
        # API kulcs beállítása
        if api_key:
            genai.configure(api_key=api_key)
        else:
            # Környezeti változóból próbálja beolvasni
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return {
                    "success": False,
                    "error": "Gemini API kulcs nincs beállítva. Állítsd be a GEMINI_API_KEY környezeti változót vagy add meg az API kulcsot."
                }
            genai.configure(api_key=api_key)
        
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
    "reasoning": "Rövid indoklás magyarul (max 2-3 mondat)"
}}"""

        # Gemini modell inicializálása
        model = genai.GenerativeModel('gemini-pro')
        
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
