# CV Filter - Audit Logging és Transzparencia

## Implementált Funkciók

### 1. Audit Logging Service (`accounts/logging_service.py`)

Központi szolgáltatás az audit logok és CV hozzáférési események kezelésére.

#### AuditLogService

3 szintű naplózás támogatása:
- **LOG**: Fontos műveletek (alapértelmezett)
- **DEBUG**: Részletes működési információk
- **VERBOSE**: Nagyon részletes diagnosztikai információk

Használat:
```python
from accounts.logging_service import AuditLogService

# Alapértelmezett LOG szintű naplózás
AuditLogService.log(
    organization=org,
    event_type='user.action',
    entity_type='cv_file',
    entity_id=cv_file.id,
    actor_user=user,
    description='CV feltöltve'
)

# DEBUG szintű naplózás
AuditLogService.debug(
    organization=org,
    event_type='api.call',
    entity_type='endpoint',
    description='API végpont hívás'
)

# VERBOSE szintű naplózás
AuditLogService.verbose(
    organization=org,
    event_type='system.process',
    entity_type='background_job',
    metadata={'details': 'teljes részletek'}
)
```

#### CVAccessEventService

CV hozzáférések és feldolgozási események nyomon követése:
```python
from accounts.logging_service import CVAccessEventService

# CV feltöltés naplózása
CVAccessEventService.log_cv_upload(
    organization=org,
    candidate=candidate,
    cv_file=cv_file,
    actor_user=user
)

# CV megtekintés naplózása
CVAccessEventService.log_cv_view(
    organization=org,
    candidate=candidate,
    cv_file=cv_file,
    actor_user=user
)
```

### 2. Automatikus Middleware (`accounts/middleware.py`)

HTTP kérések automatikus naplózása 3 szinten:

#### Naplózási szintek:

**LOG (alapértelmezett)**:
- Csak fontos műveletek: POST, PUT, DELETE, PATCH
- Csak API endpoint-ok (`/api/*`)

**DEBUG**:
- Minden API hívás (GET is)
- Részletesebb információk

**VERBOSE**:
- MINDEN kérés
- Teljes kérés és válasz részletek
- Érzékeny adatok automatikusan elfedve

#### Beállítás:

Environment változóban vagy settings.py-ban:
```python
AUDIT_LOG_LEVEL = 'LOG'  # vagy 'DEBUG', 'VERBOSE'
```

### 3. API Endpoint-ok

#### Audit Logok lekérdezése

```
GET /api/audit/logs/
```

Query paraméterek:
- `event_type`: Esemény típus szerinti szűrés
- `entity_type`: Entitás típus szerinti szűrés
- `severity`: Súlyosság szerinti szűrés (log/debug/verbose)
- `limit`: Találatok száma (max 1000, alapértelmezett 100)

Példa válasz:
```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "organization": "uuid",
      "organization_name": "Cégünk Kft",
      "actor_user": "uuid",
      "actor_username": "admin",
      "severity": "log",
      "event_type": "cv_access.uploaded",
      "entity_type": "candidate",
      "entity_id": "uuid",
      "description": "CV uploaded for John Doe",
      "metadata": {...},
      "created_at": "2026-01-14T10:00:00Z"
    }
  ]
}
```

#### CV Hozzáférési Események

```
GET /api/audit/events/
```

Query paraméterek:
- `candidate_id`: Jelölt UUID szerinti szűrés
- `action`: Művelet típus szerinti szűrés
- `limit`: Találatok száma (max 1000, alapértelmezett 100)

Példa válasz:
```json
{
  "count": 1,
  "results": [
    {
      "id": "uuid",
      "organization": "uuid",
      "actor_user": "uuid",
      "actor_username": "recruiter",
      "candidate": "uuid",
      "candidate_name": "John Doe",
      "cv_file": "uuid",
      "action": "viewed",
      "channel": "web",
      "metadata": {...},
      "created_at": "2026-01-14T10:00:00Z"
    }
  ]
}
```

### 4. Automatikus Naplózás

A rendszer automatikusan naplózza:

1. **CV feltöltéskor**: `CVUploadView`-ban automatikus event logging
2. **HTTP kérésekkor**: Middleware automatikus audit logging
3. **Fontos eseményeknél**: Service metódusok explicit naplózása

### Biztonsági Funkciók

1. **Érzékeny adatok elfedése**: 
   - Jelszavak, tokenek automatikusan `***REDACTED***`
   
2. **Szervezet izolálás**:
   - Minden log szervezethez kötött
   - Csak saját szervezet logjait lehet lekérdezni

3. **Teljesítmény védelem**:
   - Max 1000 találat egy lekérdezésben
   - Indexelt adatbázis mezők

## Használati Példák

### Környezeti változók

```bash
# Alapértelmezett (csak fontos műveletek)
AUDIT_LOG_LEVEL=LOG

# Részletes API naplózás
AUDIT_LOG_LEVEL=DEBUG

# Teljes diagnosztikai naplózás
AUDIT_LOG_LEVEL=VERBOSE
```

### Példa lekérdezések

```bash
# Összes audit log
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/audit/logs/

# Csak CV feltöltések
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/logs/?event_type=cv_access.uploaded"

# Verbose szintű logok
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/logs/?severity=verbose&limit=50"

# Egy jelölt összes hozzáférése
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/audit/events/?candidate_id=<UUID>"
```

## Adatbázis Modellek

### AuditLog
- Általános audit log minden rendszeresemény számára
- Severity szintek: LOG, DEBUG, VERBOSE
- Indexelve: organization, created_at, event_type

### CVAccessEvent
- Specifikus CV hozzáférési események
- Action típusok: viewed, uploaded, parsed, ranked, stb.
- Indexelve: organization, candidate, created_at

## Megfelelés és Transzparencia

A rendszer teljes tevékenység átláthatóságot biztosít:

✓ Minden felhasználói művelet naplózva
✓ CV hozzáférések külön nyomon követve
✓ Időbélyegek minden eseményen
✓ Metaadatok részletes kontextussal
✓ Lekérdezhető API endpoint-okkal
✓ GDPR és compliance követelmények támogatása
