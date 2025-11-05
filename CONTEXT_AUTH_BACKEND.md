# Contexte Backend Auth — Monajent (Django + DRF)

## Stack et structure
- Django 5 + Django REST Framework
- SimpleJWT (access court, refresh long) + blacklist/rotation activables
- Apps: `apps.users`, `apps.api`, `apps.core` (services)
- Base de données: SQLite (dev) — compatible PostgreSQL

## Modèles principaux (`apps.users`)
- `User`: login par téléphone, `username`/`email` optionnels, `role ∈ {CLIENT, AGENT, ADMIN}`
- `ClientProfile`: préférences, vérification téléphone, langue, device tokens
- `AgentProfile`: `agency_name`, `verified`, KYC (CNI, photo, docs)
- `AgentDocument`: fichiers rattachés à l’agent

## OTP et fournisseur
- Provider: D7 Verify (SMS OTP). Intégration via `apps/core/services/d7_verify.py`
- Orange SMS supprimé (client, commandes, webhook DLR)

## Design Auth (moderne, sécurisé)
- Access JWT (court) renvoyé en JSON et gardé en RAM côté front (Pinia)
- Refresh JWT (long) en cookie HttpOnly, SameSite=Lax (dev), rotation + blacklist prises en charge
- Aucune donnée sensible dans localStorage/sessionStorage
- CORS avec credentials et origines explicites; protection Origin/Referer sur `/auth/refresh` et `/auth/logout`

## Flux d’inscription — stateless OTP (D7)
1) `POST /api/auth/register/client|agent` → envoie OTP via D7 et renvoie un `pending_token` signé contenant:
   - phone (E.164), role, username/email/agency_name, password_hash, otp_id, `exp`
2) `POST /api/auth/otp/verify { pending_token, code }` → vérifie D7; si APPROVED:
   - crée `User` (+ `ClientProfile` ou `AgentProfile`), pose cookie refresh, renvoie `{ access }`
3) `POST /api/auth/otp/request { pending_token }` → renvoie/relance OTP (D7), renvoie un `pending_token` (mis à jour si besoin)

## Reset mot de passe — 3 étapes (stateless)
1) `POST /api/auth/password/reset/request { phone }` → renvoie `reset_token`
2) `POST /api/auth/password/reset/verify { reset_token, code }` → renvoie `reset_session_token`
3) `POST /api/auth/password/reset/finalize { reset_session_token, new_password }` → met à jour le mot de passe

## Autres endpoints auth
- `POST /api/auth/login { phone, password }` → `{ access }` + cookie refresh HttpOnly
- `POST /api/auth/refresh` (via cookie) → `{ access }` (protégé Origin/Referer)
- `POST /api/auth/logout` (Bearer requis) → 204 + suppression cookie refresh (protégé Origin/Referer)
- `GET /api/auth/me` (Bearer) → profil courant

## Sécurité (état & recommandations)
- En place:
  - HttpOnly refresh, access en RAM, CORS à origines explicites
  - Origin/Referer check sur `/auth/refresh` et `/auth/logout`
  - Blacklist de tous les refresh à `logout`
  - Zéro écriture DB avant OTP APPROVED (inscription/reset)
- À verrouiller en prod:
  - Cookies: `Secure=True` + `SameSite=None` si front ≠ domaine API; HTTPS obligatoire
  - DRF throttling: `/auth/login`, `/auth/otp/request`, `/auth/password/reset/*`
  - Password policy: longueur/complexité; éventuellement HIBP
  - Compte: lock temporaire après échecs
  - En-têtes: CSP, HSTS, Permissions-Policy, Referrer-Policy stricte
  - Rotation régulière du token D7; DEBUG=False; logs/audit centralisés

## Variables d’environnement (.env)
```
D7_API_BASE_URL=https://api.d7networks.com
D7_API_TOKEN=<token_d7_bearer>
D7_ORIGINATOR=SignOTP
```

## Notes d’intégration Front
- Toujours `withCredentials=true` pour `/auth/login` (cookie refresh), `/auth/refresh`, `/auth/logout`
- Intercepteur 401 → `/auth/refresh` → rejouer la requête
- Ne jamais persister l’`access` (RAM uniquement)

## Tests (exemples CLI)
- Register client:
```
curl -s -X POST http://localhost:8000/api/auth/register/client \
  -H 'Content-Type: application/json' \
  -d '{"phone":"0544166309","username":"dev","password":"S3cur3!pass"}'
```
- Verify OTP:
```
curl -i -c cookies.txt -X POST http://localhost:8000/api/auth/otp/verify \
  -H 'Content-Type: application/json' \
  -d '{"pending_token":"...","code":"123456"}'
```
- Refresh + Me:
```
ACCESS=$(curl -s -b cookies.txt -X POST http://localhost:8000/api/auth/refresh | \
  python3 -c 'import sys,json; print(json.load(sys.stdin)["access"])' | tr -d '\r\n ')
curl -s -H "Authorization: Bearer $ACCESS" http://localhost:8000/api/auth/me
```
- Logout:
```
curl -i -H "Authorization: Bearer $ACCESS" -X POST http://localhost:8000/api/auth/logout
```

## Fichiers clés
- `apps/api/views/auth.py`, `apps/api/serializers/auth.py`, `apps/api/urls.py`
- `apps/users/models.py`
- `apps/core/services/d7_verify.py`



