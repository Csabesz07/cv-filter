# CV Filter - Kipróbálási Útmutató

## 🚀 Termék Elérése

### Lokális Telepítés (Ajánlott kipróbáláshoz)

#### Előfeltételek
- Docker Desktop telepítve és futva
- Git telepítve

#### Lépések

1. **Repository klónozása**
   ```bash
   git clone https://github.com/edme02/cv-filter.git
   cd cv-filter
   ```

2. **Környezeti változók beállítása**
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

3. **Alkalmazás indítása**
   ```bash
   docker-compose up --build
   ```
   
   Várjon, amíg minden service elindul (2-3 perc)

4. **Alkalmazás elérése**
   - **Frontend**: http://localhost:5173
   - **Backend API**: http://localhost:8000
   - **Django Admin**: http://localhost:8000/admin

---

## 👤 Tesztelési Útmutató

### 1. Felhasználó Regisztráció

**Webes felület:**
- Nyissa meg: http://localhost:5173/register
- Töltse ki a regisztrációs formot:
  - Username: `testuser`
  - Email: `test@example.com`
  - Password: `TestPass123!`
  - Organization: `TestOrg`

**Vagy API-n keresztül:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "organization": "TestOrg"
  }'
```

### 2. Bejelentkezés

**Webes felület:**
- http://localhost:5173/login
- Használja a regisztrált felhasználónevet és jelszót

**API:**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'
```

Válasz (mentse el az `access` tokent):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

### 3. CV Feltöltés

**API (használja a kapott access tokent):**
```bash
curl -X POST http://localhost:8000/api/candidates/upload-cv/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@path/to/cv.pdf" \
  -F "first_name=John" \
  -F "last_name=Doe"
```

**Webes felület:**
- Navigáljon: http://localhost:5173/candidates
- Kattintson "Upload CV" gombra
- Válasszon PDF/DOCX fájlt

### 4. Ranking Futtatás

**API:**
```bash
curl -X POST http://localhost:8000/api/ranking/create/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "criteria": {
      "required_skills": ["Python", "Django"],
      "preferred_skills": ["Docker", "React"],
      "min_experience_years": 2,
      "required_level": "bachelor"
    },
    "bias_config": {
      "skill_weight": 0.6,
      "experience_weight": 0.3,
      "education_weight": 0.1
    }
  }'
```

Válasz:
```json
{
  "ranking_run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2026-01-20T19:00:00Z"
}
```

### 5. Ranking Eredmények Lekérése

```bash
curl -X GET http://localhost:8000/api/ranking/550e8400-e29b-41d4-a716-446655440000/results/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 6. CV Összefoglalás Generálása

```bash
curl -X POST http://localhost:8000/api/candidates/CANDIDATE_ID/summary/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "style": "professional",
    "max_length": 200
  }'
```

---

## 📊 Demo Adatok

A rendszerben található **minta CV-k** a `samples/` könyvtárban:
- `samples/cvs_en/` - Angol nyelvű CV-k
- `samples/cvs_hu/` - Magyar nyelvű CV-k

Feltölthet ezeket teszteléshez!

---

## 🔍 Főbb Funkciók Kipróbálása

### ✅ Funkció Lista

1. **Felhasználó kezelés**
   - Regisztráció ✅
   - Bejelentkezés ✅
   - JWT alapú autentikáció ✅

2. **CV feldolgozás**
   - PDF/DOCX feltöltés ✅
   - Automatikus szöveg kinyerés ✅
   - Entitás felismerés (skills, experience, education) ✅

3. **Jelölt Ranking**
   - Kritériumok alapú szűrés ✅
   - Súlyozott pontozás ✅
   - Bias detektálás ✅
   - Részletes magyarázatok ✅

4. **CV Összefoglalás**
   - AI alapú összefoglalás ✅
   - Stílus választás ✅
   - Hossz kontroll ✅

5. **Audit Logging**
   - Minden művelet naplózása ✅
   - Esemény kategorizálás ✅
   - Severity szintek ✅

---

## 🛠️ Hibaelhárítás

### Docker nem indul el
```bash
# Windows
Restart-Service docker

# Linux/Mac
sudo systemctl restart docker
```

### Port már foglalt (5173 vagy 8000)
```bash
# Windows - kill process on port
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Linux/Mac
lsof -ti:8000 | xargs kill
```

### Migráció hibák
```bash
# Törölje az adatbázis volume-ot és indítsa újra
docker-compose down -v
docker-compose up --build
```

---

## 📞 Támogatás

- **Dokumentáció**: `docs/` könyvtár
- **API példák**: `docs/api/`
- **GitHub Issues**: https://github.com/edme02/cv-filter/issues

---

## 🧪 CI/CD Státusz

[![CICD](https://github.com/edme02/cv-filter/actions/workflows/cicd.yml/badge.svg)](https://github.com/edme02/cv-filter/actions/workflows/cicd.yml)

A projekt minden commit után automatikusan tesztelve van:
- ✅ 19 unit teszt
- ✅ PostgreSQL pgvector integráció
- ✅ Docker build
- ✅ Image publikálás (ghcr.io)
