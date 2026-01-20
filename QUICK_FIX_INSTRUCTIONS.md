# GYORS JAVÍTÁS - Token Probléma

## A probléma
A tokenek lejártak vagy érvénytelenek. A refresh token is valószínűleg lejárt.

## Megoldás (3 lehetőség)

### 1. LEGJOBB: Böngésző konzolban (F12)
Nyisd meg a böngészőben az F12-t, majd írd be a Console fülön:

```javascript
// Tokenek törlése
sessionStorage.clear();
localStorage.clear();
// Újratöltés
window.location.href = '/login';
```

### 2. A Logout gomb használata
1. Kattints a jobb felső sarokban a **Logout** gombra
2. Jelentkezz be újra

### 3. Manuális storage törlés
F12 → Application/Storage fül:
- Session Storage → töröld az összes kulcsot
- Local Storage → töröld az összes kulcsot
- Frissítsd az oldalt (F5)

## Utána
1. Menj a `/login` oldalra
2. Jelentkezz be újra
3. Most már működni fog az "Uploaded files" fül automatikus token frissítéssel

## Debug információk megtekintése
Ha szeretnéd látni mi történik a háttérben:
1. Nyisd meg az F12-t
2. Menj a Console fülre  
3. Kattints az "Uploaded files" fülre
4. Lásd az üzeneteket:
   - "Making authenticated request to..."
   - "Received 401, attempting token refresh..."
   - "Attempting to refresh access token..."
