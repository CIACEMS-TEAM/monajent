# Contexte MonaJent — Bilan technique complet

## 1. Vue d'ensemble du projet

**MonaJent** est une plateforme immobilière ivoirienne (Côte d'Ivoire) permettant aux agents immobiliers de publier des annonces avec photos/vidéos, et aux clients de rechercher des biens, visionner des vidéos (via un système de clés virtuelles payantes), et demander des visites physiques gratuites.

- **Backend** : Django 5 + DRF + PostgreSQL + Redis + Celery
- **Frontend** : Vue 3 + TypeScript + Vite 7 + Pinia + PrimeVue 4
- **Déploiement** : Dokploy sur VPS, Traefik reverse proxy, Docker (images `ciacems/mjt:backend` et `ciacems/mjt:frontend`)
- **Stockage média** : Cloudflare R2 (S3-compatible) en production, FileSystem en dev
- **Paiement** : Paystack (principal), architecture multi-gateway (CinetPay, Flutterwave, Moneroo en config)
- **SMS/OTP** : Orange SMS CI + D7 Networks pour vérification
- **Domaines** : `monajent.com` (frontend), `api.monajent.com` (backend API)
- **Branche active** : `mvpsenior` sur `github.com/CIACEMS-TEAM/monajent.git`

---

## 2. Structure du projet

```
monajent/
├── backend/                  # Django project
│   ├── config/               # settings.py, urls.py, wsgi.py
│   ├── apps/
│   │   ├── api/              # DRF serializers/, views/, urls.py, throttles
│   │   ├── core/             # Services métier (payment_gateway, video_dedup, video_thumbnail, viewing, visits, withdrawal, orange_sms, d7_verify)
│   │   ├── users/            # User, ClientProfile, AgentProfile, AgentDocument, LegalConsent, Notification
│   │   ├── listings/         # Listing, ListingImage, Video, ListingReport
│   │   ├── packs/            # PackPurchase, VirtualKeyUsage
│   │   ├── wallet/           # Wallet, WalletEntry, PlatformRevenue, WithdrawalRequest
│   │   ├── visits/           # AgentAvailabilitySlot, AgentDateSlot, VisitRequest
│   │   ├── payments/         # Payment
│   │   ├── support/          # SupportTicket, SupportMessage
│   │   └── favorites/        # FavoriteListing, SavedSearch
│   ├── Dockerfile, entrypoint.sh, requirements.txt
│   └── manage.py
├── frontend/                 # Vue 3 + Vite
│   ├── src/
│   │   ├── Stores/           # auth.ts, agent.ts, client.ts, public.ts, notifications.ts, support.ts
│   │   ├── services/http.ts  # Axios instance + interceptors JWT refresh
│   │   ├── router/index.ts   # Routes + guards
│   │   ├── views/            # 28 .vue files (public, auth, client, agent, legal, support)
│   │   ├── components/       # ShareDialog, ListingFormDialog, ListingDetailDialog, MapPicker, etc.
│   │   └── layouts/AgentLayout.vue
│   ├── Dockerfile, nginx.conf, index.html
│   └── package.json
├── docker/backup/            # Backup scripts
├── docker-compose.yml        # Dev: Postgres + Redis
├── docker-compose.build.yml  # Build: backend + frontend images
└── .env                      # Dev environment
```

---

## 3. Modèles principaux (Backend Django)

### User (AUTH_USER_MODEL = 'users.User')
- `phone` (unique, E.164), `username`, `email`, `role` (CLIENT/AGENT/ADMIN)
- Profils séparés : `ClientProfile` (1-1), `AgentProfile` (1-1, KYC, agency_name, verified)
- `AgentDocument` (CNI recto/verso, passeport), `LegalConsent`, `Notification`

### Listing
- `agent` (FK User AGENT), `title`, `slug` (unique, auto-généré depuis titre+ville), `description`
- `listing_type` (LOCATION/VENTE), `status` (ACTIF/INACTIF/EXPIRED/SUSPENDED/DELETED)
- Localisation : `city`, `neighborhood`, `address`, `latitude`, `longitude`
- Prix : `price` (XOF), `deposit_months`, `advance_months`, `agency_fee_months`
- Caractéristiques : `rooms`, `bedrooms`, `bathrooms`, `surface_m2`, `furnishing`, `amenities` (JSON)
- Compteurs dénormalisés : `views_count`, `favorites_count`, `reports_count`
- Dates : `published_at`, `expires_at` (7 jours par défaut), `created_at`, `updated_at`
- Images (`ListingImage`), Vidéos (`Video` avec `access_key` UUID, `file_hash`, `perceptual_hash`)

### Système de paiement/visionnage
- `PackPurchase` : un achat = X clés virtuelles + 1 clé physique (visite)
- `VirtualKeyUsage` : 1 clé = 1 vidéo débloquée, revenus split agent/plateforme
- `Payment` : provider (PAYSTACK, ORANGE_MONEY, etc.), tx_ref, statut
- `Wallet` + `WalletEntry` : solde agent, retraits (`WithdrawalRequest`)

### Visites
- `AgentAvailabilitySlot` / `AgentDateSlot` : créneaux de disponibilité
- `VisitRequest` : client demande visite → agent confirme → code de vérification → validation

---

## 4. API Endpoints principaux (préfixe /api/)

### Auth
- POST `auth/register/client`, `auth/register/agent`, `auth/login`, `auth/refresh`, `auth/logout`
- GET `auth/me`
- POST `auth/otp/request`, `auth/otp/verify`
- POST `auth/password/reset/request`, `auth/password/reset/verify`, `auth/password/reset/finalize`, `auth/password/change`

### Public
- GET `listings/` (liste paginée, filtres), `listings/<slug>/` (détail)
- GET `sitemap.xml`, `share/<slug>/` (OG tags pour partage social)

### Agent
- CRUD `agent/listings/`, images, vidéos, renouvellement, bulk actions
- GET/PUT `agent/profile/`, KYC submit, documents
- CRUD `agent/availability/`, `agent/date-slots/`
- GET `agent/visits/`, confirm/validate-code/no-show
- GET `agent/wallet/`, entries, withdrawals, set-pin, change-pin, withdraw
- GET `agent/dashboard/`, `agent/analytics/`

### Client
- GET `client/dashboard/`, `client/profile/`
- CRUD `client/packs/`, `client/favorites/`, `client/saved-searches/`
- POST `client/packs/buy/` (initie paiement Paystack)
- GET `client/views/` (historique vidéos), `client/visits/`, `client/reports/`
- POST `videos/<uuid>/teaser/`, `videos/<uuid>/watch/`

### Paiements
- POST `payments/webhook/` (Paystack webhook, IP whitelisting)
- GET `payments/verify/<tx_ref>/`

### Support
- CRUD `support/tickets/`, messages, close

---

## 5. Frontend — Routes et architecture

### Routes publiques
- `/home` → `HomeListings` (liste d'annonces)
- `/home/annonce/:slug` → `PublicListingView` (détail annonce, teaser vidéo, partage)
- `/auth/login`, `/auth/join`, `/auth/signup/client`, `/auth/signup/agent`
- `/legal/cgu`, `/legal/confidentialite`, `/legal/conditions-agents`

### Routes client (requiresClient)
- `/home/dashboard`, `/home/favorites`, `/home/history`, `/home/packs`, `/home/payments`, `/home/visits`, `/home/reports`, `/home/profile`, `/home/support`

### Routes agent (requiresAgent)
- `/agent/onboarding` (si profil incomplet)
- `/agent` → `AgentDashboard`
- `/agent/listings`, `/agent/analytics`, `/agent/visits`, `/agent/wallet`, `/agent/settings`, `/agent/support`

### Stores Pinia
- `auth` : JWT (access en RAM, refresh en cookie HttpOnly), bootstrap, login/register/OTP
- `public` : listings publiques, favoris, vidéo teaser/watch, clés virtuelles
- `agent` : profil, KYC, listings CRUD, wallet, visites, disponibilités, dashboard, analytics
- `client` : profil client, dashboard
- `notifications` : liste, read, unread-count
- `support` : tickets

### HTTP (services/http.ts)
- Axios avec `baseURL` = `VITE_API_BASE_URL` (ou `window.location.origin`)
- `withCredentials: true` pour cookie refresh HttpOnly
- Interceptor request : ajoute `Authorization: Bearer <accessToken>`
- Interceptor response : refresh automatique sur 401, queue des requêtes pendant refresh, forceLogout si refresh échoue

---

## 6. Déploiement Docker

### Backend Dockerfile
- Multi-stage : builder (requirements.txt + gcc/libpq-dev), runtime (python:3.12-slim + ffmpeg)
- `entrypoint.sh`, expose 8000

### Frontend Dockerfile
- 3 stages : deps (npm ci), build (vite build avec VITE_API_BASE_URL et VITE_PAYSTACK_PUBLIC_KEY), runtime (nginx:1.27-alpine)
- `envsubst` au build pour injecter `API_PROXY_URL` dans nginx.conf
- User non-root `app`, expose 80

### nginx.conf (frontend)
- Gzip, cache immutable 1y pour JS/CSS, 30d pour images
- `location /share/` → proxy_pass vers backend (OG tags pour partage social)
- SPA fallback `try_files $uri $uri/ /index.html`
- Sécurité : blocage dotfiles/wp-*, headers X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy

---

## 7. Configuration (settings.py — points clés)

- `AUTH_USER_MODEL = 'users.User'`
- JWT : access 10min, refresh 14 jours, rotate + blacklist
- REST_FRAMEWORK : pagination 20, throttles par scope
- Storage : FileSystem par défaut, S3Boto3Storage (Cloudflare R2) si `USE_R2=True`
- Paiement multi-gateway : `PAYMENT_GATEWAY` + `PAYMENT_CONFIG` dict
- Celery : eager si pas de broker Redis
- CORS/CSRF depuis env
- `FRONTEND_URL` : utilisé pour sitemap, share OG, emails
- Logging : console + rotating file `backend/logs/monajent.log`

---

## 8. Travaux récemment terminés (dernier commit)

1. **Performance frontend** : images optimisées en WebP, favicon réduit, compression gzip, cache nginx
2. **SEO** : `<meta description>`, `robots.txt`, sitemap statique + dynamique Django, `<html lang="fr">`
3. **URLs SEO-friendly** : `SlugField` sur Listing + migration données existantes, routes `/home/annonce/:slug`
4. **Partage social riche** : endpoint `share.py` (détection bots User-Agent → page HTML OG / redirect 302 pour humains), aperçu image+titre+prix sur WhatsApp/Facebook
5. **Proxy nginx /share/** : l'URL partagée est `monajent.com/share/<slug>/` (pas `api.monajent.com`)
6. **"Visite Gratuite !"** dans les messages de partage et la description OG
7. **Webhook Paystack** : fix IP derrière reverse proxy (X-Forwarded-For)
8. **Sécurité nginx** : blocage dotfiles, headers sécurité, cache control

---

## 9. Technologies et dépendances clés

### Backend
Django 5, DRF, django-filter, drf-spectacular (OpenAPI), django-cors-headers, djangorestframework-simplejwt, django-storages (S3/R2), django-environ, whitenoise, daphne (ASGI), celery, Pillow, ffmpeg (thumbnails vidéo), sentry-sdk

### Frontend
Vue 3.5, TypeScript 5.9, Vite 7, Pinia 3, Vue Router 4, PrimeVue 4 (@primeuix/themes), Axios, Leaflet (cartes), vue-toastification, vue-multiselect

---

## 10. Conventions de code

- **Langue** : interface utilisateur et commentaires en français, code en anglais
- **Backend** : apps séparées par domaine, serializers/views dans le module `api`, services métier dans `core/services/`
- **Frontend** : Stores Pinia dans `src/Stores/`, composants dans `src/components/`, vues dans `src/views/`, service HTTP centralisé dans `src/services/http.ts`
- **Commits** : format `type: description en français` (feat, fix, chore)
- **Git** : branche `mvpsenior`, pas de tags de release pour l'instant
