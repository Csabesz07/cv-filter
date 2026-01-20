# CV Összefoglaló API - Példák

## API Endpoint

```
POST /api/candidates/{candidate_id}/summary/
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## 1. Alapértelmezett használat (Template-based, Magyar)

### Request
```bash
curl -X POST http://localhost:8000/api/candidates/550e8400-e29b-41d4-a716-446655440000/summary/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Response (200 OK)
```json
{
  "summary": "A jelölt Senior Software Engineer pozícióban dolgozik, tapasztalattal rendelkezik a következő területeken: Backend Developer, Team Lead. A jelölt jól ért a következő programozási nyelvekhez: Python, Java, Javascript, C++, tapasztalt a következő keretrendszerekkel: Django, React, Spring Boot. A jelölt tapasztalattal rendelkezik eszközök, mint például Git, Docker, Kubernetes, felhő platformok, mint például Aws, Azure használatában. A jelölt Informatikai Mérnök Bsc, Adattudományi Msc végzettséggel rendelkezik, rendelkezik Aws Certified Solutions Architect, Scrum Master. A jelölt részletes Csapatmunka, Kommunikáció, Problémamegoldás készségekkel rendelkezik.",
  "highlights": [],
  "risks": [],
  "fit_score_explanation": "",
  "method": "template"
}
```

## 2. Angol nyelvű összefoglaló

### Request
```bash
curl -X POST http://localhost:8000/api/candidates/550e8400-e29b-41d4-a716-446655440000/summary/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en"
  }'
```

### Response (200 OK)
```json
{
  "summary": "The candidate is a Full Stack Developer with experience in Software Engineer. The candidate is proficient in Python, Javascript, Typescript, Go, experienced with React, Node.Js, Fastapi. The candidate has experience with tools such as Git, Docker, cloud platforms including Aws. The candidate holds Computer Science Bsc, has Aws Certified Developer. The candidate demonstrates Leadership, Communication.",
  "highlights": [],
  "risks": [],
  "fit_score_explanation": "",
  "method": "template"
}
```

## 3. AI-alapú összefoglaló (Make.com webhook)

### Request
```bash
curl -X POST http://localhost:8000/api/candidates/550e8400-e29b-41d4-a716-446655440000/summary/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "language": "hu",
    "method": "ai",
    "job_text": "Senior Python fejlesztőt keresünk Django tapasztalattal."
  }'
```

### Response (200 OK)
```json
{
  "summary": "Tapasztalt Python fejlesztő, aki több éves Django keretrendszeres munkával rendelkezik...",
  "highlights": ["Erős Django ismeret", "AWS tapasztalat"],
  "risks": ["Kevés frontend tapasztalat"],
  "fit_score_explanation": "A jelölt jól illeszkedik a pozícióhoz...",
  "method": "ai"
}
```

## 4. Hibakezelés

### A) Nincs strukturált adat
```json
{
  "detail": "No structured data available for this candidate. Please ensure CV has been processed."
}
```
**Status:** 400 BAD REQUEST

### B) Nem található jelölt
```json
{
  "detail": "Candidate not found."
}
```
**Status:** 404 NOT FOUND

### C) Nincs jogosultság
```json
{
  "detail": "User has no organization."
}
```
**Status:** 403 FORBIDDEN

### D) Nincs parse-olt CV
```json
{
  "detail": "No parsed CV text available for this candidate."
}
```
**Status:** 400 BAD REQUEST

### E) Generálás sikertelen
```json
{
  "detail": "Summary generation failed: Connection timeout"
}
```
**Status:** 502 BAD GATEWAY

## 5. Cache használat

Az API automatikusan cache-eli az összefoglalókat. Ha ugyanazokkal a paraméterekkel kérsz újra összefoglalót, a cache-elt verzió jön vissza azonnal.

Cache kulcs komponensek:
- Szervezet
- Jelölt
- CV parse verzió
- Nyelv
- Módszer (template/ai)

Új CV feltöltésekor új összefoglaló generálódik.

## 6. JavaScript példa (Frontend)

```javascript
async function generateCandidateSummary(candidateId, language = 'hu') {
  try {
    const response = await fetch(
      `/api/candidates/${candidateId}/summary/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          language: language,
          method: 'template'  // hallucinációmentes
        })
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Összefoglaló generálása sikertelen');
    }

    const data = await response.json();
    console.log('Összefoglaló:', data.summary);
    return data;
    
  } catch (error) {
    console.error('Hiba:', error.message);
    throw error;
  }
}

// Használat:
generateCandidateSummary('550e8400-e29b-41d4-a716-446655440000', 'hu')
  .then(data => {
    document.getElementById('summary-text').textContent = data.summary;
  })
  .catch(error => {
    alert('Hiba történt: ' + error.message);
  });
```

## 7. Python példa (Backend/Script)

```python
import requests

def get_candidate_summary(candidate_id: str, token: str, language: str = "hu"):
    """
    Jelölt összefoglalójának lekérése.
    
    Args:
        candidate_id: UUID of the candidate
        token: JWT authentication token
        language: Summary language ('hu' or 'en')
    
    Returns:
        dict: Summary response
    """
    url = f"http://localhost:8000/api/candidates/{candidate_id}/summary/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "language": language,
        "method": "template"  # hallucinációmentes
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    return response.json()

# Használat:
summary_data = get_candidate_summary(
    candidate_id="550e8400-e29b-41d4-a716-446655440000",
    token="eyJ0eXAiOiJKV1QiLCJhbGc...",
    language="hu"
)

print(f"Összefoglaló: {summary_data['summary']}")
```

## 8. Audit logging

Minden összefoglaló generálás automatikusan naplózva van:

- **Action:** `SUMMARY_GENERATED`
- **Actor:** A bejelentkezett felhasználó
- **Target:** A jelölt
- **Metadata:**
  ```json
  {
    "language": "hu",
    "method": "template",
    "prompt_version": "v1.0"
  }
  ```

Lekérdezés:
```
GET /api/audit/events/?action=SUMMARY_GENERATED
```

## Összegzés

A CV összefoglaló API egyszerű használatú, biztonságos és rugalmas megoldás. Az alapértelmezett template-based módszer garantáltan hallucinációmentes, míg az opcionális AI-alapú módszer kreatívabb eredményeket ad. A cache mechanizmus gyors válaszidőt biztosít ismételt kéréseknél.
