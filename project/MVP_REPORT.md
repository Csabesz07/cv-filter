MVP dokumentacio

1) Hivatkozas es instrukcio a kiprobalhato termekre
- Helyi futtatas (Docker): `docker-compose up --build`
  - Backend eleres: http://localhost:8000
  - Auth kepernyok: `/login/` es `/register/`
- Helyi futtatas (Docker nelkul): `pip install -r requirements.txt`, majd
  `python cv_filter/manage.py migrate` es `python cv_filter/manage.py runserver`
- Referencia: `README.md` (reszletes leiras)

2) VCS, CI, bugtracker/agile es hasznalt eszkozok
- Version Control System: GitHub repo
  - https://github.com/edme02/cv-filter
- CI: GitHub Actions workflow
  - `.github/workflows/cicd.yml` (tesztek + Docker build)
- Bugtracker/agile eszkoz: Jira
  - https://jocman0305.atlassian.net/jira/software/c/projects/CP/boards/3
1) User story statusz (MVP vs nem MVP)
Az MVP-ben kijelolt user story-k a kovetkezok: Joel-02, Edit-01, Peter-01, Peter-02, Edit-02.

MVP user story-k:
| ID | Statusz | Megvalositas roviden | Bizonyitek |
| --- | --- | --- | --- |
| Joel-02 | Reszben | CV fajl feltoltes es szoveg kinyeres (PDF/DOCX) megvan, de strukturalt kompetencia-kigyujtes es LinkedIn integracio nincs bekotve. | `cv_filter/accounts/views.py`, `cv_filter/document_extraction/extract_data.py`, `cv_filter/accounts/models.py` |
| Edit-01 | Kesz | AI-alapu rangsorolas es scoring API megvan. | `cv_filter/ranking/services.py`, `cv_filter/ranking/views.py`, `RANKING_EVENTS_API.md` |
| Peter-01 | Kesz | Termeszetes nyelvu kereses: NLQ parse endpoint + keresesi szurok es pontozas. | `cv_filter/accounts/views.py`, `cv_filter/accounts/ai.py` |
| Peter-02 | Kesz | Automatikus jelolt-osszefoglalo generalas (Make webhook). | `cv_filter/accounts/views.py`, `cv_filter/accounts/ai.py` |
| Edit-02 | Kesz (MVP scope) | Hatterszintu naplozas es ranking event logok elerhetok, nincs valos ideju dashboard. | `cv_filter/accounts/logging_service.py`, `cv_filter/accounts/middleware.py`, `TASK_4.2_IMPLEMENTATION.md` |

Nem MVP user story-k:
| ID | Statusz | Megjegyzes |
| --- | --- | --- |
| Edit-03 | Nem kesz | Megoszthato szuresi profilok/sablonok es API-hozzaferes nincs. |
| Joel-01 | Nem kesz | Lokacio anonimizalas nincs megvalositva. |
| Joel-03 | Nem kesz | AI pozicioajanlo motor nincs. |
| Peter-03 | Nem kesz | Adaptiv ajanlorendszer (korabbi dontesekbol tanulas) nincs. |

4) Felhasznaloi statisztikak es KPI
KPI cel:
- Legalabb 1 celcsoportbeli (KKV vezeto vagy HR szakember) felhasznalo visszajelzes a szemeszter vegeig.

KPI szamitas:
- KPI teljesul, ha visszajelzesek szama >= 1.
- A repoban nincs dokumentalt visszajelzes vagy user statisztika.
- Jelenlegi allapot: KPI még nem igazolt

Megjegyzes:
- A projekt ket tagja (Kapas Adam es Suli Kristof) kilepett, emiatt jelentosen csuszott a fejlesztes, es ez kihatott a KPI eleresere is.

Felhasznaloi statisztikak:
- Nincs bevezetett telemetria/analytics a repoban.
- Audit logok es ranking event naplok elerhetok az API-n keresztul, ha statisztikat szeretnetek szamolni:
  - `LOGGING_QUICKSTART.md`, `RANKING_EVENTS_API.md`
