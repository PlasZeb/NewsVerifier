# NewsVerifier - LLM Integráció

## 🆕 LLM-alapú Hírellenőrzés

Az eredeti ML modell mellé mostmár **Google Gemini AI-alapú ellenőrzés** is elérhető!

### Beállítás

1. **Gemini API kulcs beszerzése:**
   - Látogass el ide: https://makersuite.google.com/app/apikey
   - vagy: https://aistudio.google.com/app/apikey
   - Regisztrálj Google fiókkal és generálj egy ingyenes API kulcsot
   
2. **API kulcs beállítása (2 lehetőség):**

   **A) .env fájlban (ajánlott):**
   ```bash
   cp .env.example .env
   # Szerkeszd a .env fájlt és add meg az API kulcsot
   nano .env
   ```
   
   A `.env` fájlban:
   ```
   GEMINI_API_KEY=your-actual-api-key-here
   ```

   **B) Közvetlenül az alkalmazásban:**
   - Indítsd el az alkalmazást
   - A bal oldali sidebar-ban jelöld be az "LLM alapú ellenőrzés használata" opciót
   - Add meg az API kulcsot a megjelenő mezőben

3. **Telepítés:**
   ```bash
   pip install -r requirements.txt
   ```

### Használat

1. Indítsd el az alkalmazást:
   ```bash
   streamlit run app.py
   ```

2. A bal oldali sidebar-ban:
   - Jelöld be az "LLM alapú ellenőrzés használata" opciót
   - Add meg a Gemini API kulcsot (ha még nincs beállítva)

3. Használd a szokásos módon:
   - **Input módban**: Írd be vagy másold be a hírt
   - **URL módban**: Add meg a hír URL-jét
   
4. Az eredmények:
   - **ML Model Eredmény**: Az eredeti gépi tanulás alapú osztályozás
   - **LLM Alapú Elemzés**: A Google Gemini részletes elemzése, indoklással

### Funkciók

- ✅ **Kettős ellenőrzés**: ML modell + Gemini LLM együttes használata
- ✅ **Részletes indoklás**: A Gemini megmagyarázza a döntését
- ✅ **Bizonyossági szint**: HIGH/MEDIUM/LOW értékelés
- ✅ **Három kategória**: REAL/FAKE/UNCERTAIN
- ✅ **Eredeti kód érintetlen**: Az új funkció nem módosítja az eredeti működést

### Különbségek ML vs Gemini LLM

| Szempont | ML Model | Gemini LLM |
|----------|----------|------------|
| Sebesség | ⚡ Nagyon gyors | 🐌 Lassabb (API hívás) |
| Költség | 💚 Ingyenes | 💚 Ingyenes kvóta* |
| Indoklás | ❌ Nincs | ✅ Részletes |
| Kontextus | ⚠️ Korlátozott | ✅ Mélyebb elemzés |
| Offline | ✅ Működik | ❌ Internet kell |

*A Gemini API ingyenes kvótával rendelkezik a legtöbb használati esethez

### Javasolt használat

- **Gyors ellenőrzés**: Használd csak az ML modellt
- **Részletes elemzés**: Kapcsold be a Gemini LLM-et is
- **Bizonytalan esetekben**: A Gemini segíthet a döntésben

### Költségek

A Google Gemini API **ingyenes kvótát** biztosít:
- **Gemini Pro**: 60 kérés/perc ingyenesen
- Részletek: https://ai.google.dev/pricing

A legtöbb személyes használatra ez bőven elegendő!

### Hibaelhárítás

**"Gemini API kulcs nincs beállítva"**
- Ellenőrizd, hogy helyesen állítottad-e be az API kulcsot
- Próbáld meg közvetlenül az alkalmazásban megadni
- Streamlit Cloud esetén: add hozzá a titkokhoz (Settings → Secrets → GEMINI_API_KEY)

### Streamlit Cloud Secrets

Streamlit Cloud deploy esetén a `.env` fájl nem töltődik be. Használd a Cloud titkokat:

1. Nyisd meg a projektedet a Streamlit Cloudon
2. Jobb alsó sarok: "Manage app" → Settings → Secrets
3. Adj hozzá egy új titkot:
   - Kulcs: `GEMINI_API_KEY`
   - Érték: a tényleges Gemini API kulcsod
4. Indítsd újra az appot, hogy a titok elérhető legyen

Az alkalmazás automatikusan felismeri a Streamlit Secrets-ből vagy a környezetből érkező kulcsot.

**"Rate limit exceeded"**
- Túl sok kérést küldtél rövid időn belül (60/perc limit)
- Várj egy kicsit és próbáld újra

**"API key invalid"**
- Ellenőrizd, hogy helyes API kulcsot adtál-e meg
- Generálj új kulcsot: https://aistudio.google.com/app/apikey
