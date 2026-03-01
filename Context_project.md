MONAJENT – Contexte complet pour LLM
=====================================
Dernière mise à jour : 2026-02-18

# 1. Vision produit

Monajent = premier modèle africain de **Pay-Per-View immobilier**.
- Un **client** paie 500 XOF pour un pack de **33 clés virtuelles + 1 clé physique**.
- Chaque visionnage d'une vidéo d'un bien consomme 1 clé virtuelle.
- L'**agent** reçoit **10 XOF** par visionnage, la **plateforme** retient **5 XOF**.
- La clé physique permet une visite gratuite chez l'agent.
- Marché cible : Côte d'Ivoire (Orange Money, Wave, MTN).

---

# 2. Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend | Django 5.2 + Django REST Framework + SimpleJWT |
| BDD | SQLite (dev), PostgreSQL-ready |
| Auth | JWT access (RAM) + refresh HttpOnly cookie + OTP via D7 Verify |
| Stockage médias | Local (dev), Cloudflare R2 (prod) via django-storages |
| Paiement | Architecture provider-agnostic (SimulationGateway en dev) |
| Frontend | **Non commencé** — prévu Vue.js + Pinia |

---

# 3. Arborescence backendbackend

```
monajent/backend/
├── config/               settings.py, urls.py
├── apps/
│   ├── api/              Point d'entrée REST
│   │   ├── urls.py       47 routes
│   │   ├── throttles.py  8 throttles
│   │   ├── serializers/  auth, listings, packs, payments, visits, wallet, client
│   │   └── views/        auth, listings, packs, payments, visits, wallet, client
│   ├── core/             Logique transversale
│   │   ├── permissions.py   11 permissions (IsAgent, IsClient, IsAdmin…)
│   │   ├── validators.py    StrongPasswordValidator
│   │   ├── services/        8 modules de services métier
│   │   └── management/commands/  expire_listings, auto_cancel_visits, cleanup_media
│   ├── users/            User, ClientProfile, AgentProfile, AgentDocument
│   ├── listings/         Listing, ListingImage, Video, ListingReport
│   ├── packs/            PackPurchase, VirtualKeyUsage
│   ├── wallet/           Wallet, WalletEntry, PlatformRevenue, WithdrawalRequest
│   ├── visits/           AgentAvailabilitySlot, VisitRequest
│   ├── payments/         Payment
│   └── favorites/        FavoriteListing, SavedSearch
```

---

# 4. Modèles (14 tables principales)

## Acteurs
- **User** : login par téléphone, role ∈ {CLIENT, AGENT, ADMIN}
- **ClientProfile** : préférences (JSON), whatsapp, intent, budget, villes
- **AgentProfile** : agency_name, verified, bio, KYC
- **AgentDocument** : fichiers CNI/photos rattachés à un agent

## Biens & Médias
- **Listing** : titre, type (LOCATION/VENTE), prix, ville, quartier, coords, statut, expires_at, video_hash
- **ListingImage** : FK listing, fichier image
- **Video** : FK listing, fichier, thumbnail, duration_sec, access_key (UUID), file_hash (SHA-256 anti-fraude)
- **ListingReport** : signalement client (ALREADY_TAKEN, FRAUD, INAPPROPRIATE…)

## Packs & Revenus
- **PackPurchase** : user(CLIENT), 500 XOF, 33 virtual_keys + 1 physical_key, is_locked_by_visit
- **VirtualKeyUsage** : 1 vue = 1 clé consommée, UNIQUE(pack, video, user), amounts tracés
- **Wallet** : agent, balance, total_earned, total_withdrawn, withdrawal_pin_hash
- **WalletEntry** : CREDIT/DEBIT, source (VIDEO_VIEW, PHYSICAL_VISIT, WITHDRAWAL, ADJUSTMENT)
- **PlatformRevenue** : 5 XOF par vue/visite, source (VIDEO_VIEW, PHYSICAL_VISIT)
- **WithdrawalRequest** : PENDING/COMPLETED/REJECTED, method (ORANGE_MONEY/WAVE/MTN), phone

## Visites
- **AgentAvailabilitySlot** : créneaux récurrents (jour, heure début/fin)
- **VisitRequest** : statut, code de vérification (5 chars alphanumériques), slot, virtual_key_consumed

## Paiements
- **Payment** : pack (nullable → créé après webhook), provider, tx_ref, provider_tx_id, checkout_url, status

## Favoris
- **FavoriteListing** : UNIQUE(user, listing)
- **SavedSearch** : label + filters (JSON)

---

# 5. Services métier (apps/core/services/)

| Service | Rôle |
|---------|------|
| `viewing.py` | consume_virtual_key() — transaction atomique : -1 clé, +10 agent, +5 plateforme |
| `visits.py` | request_visit(), confirm_visit(), validate_visit_code(), cancel_visit(), expire_unresponded_visits() |
| `withdrawal.py` | set/change_withdrawal_pin(), request_withdrawal() (PIN + seuil 2000 XOF), approve/reject |
| `payment.py` | initiate_pack_purchase(), process_webhook(), execute_payout() |
| `payment_gateway.py` | BasePaymentGateway (ABC), SimulationGateway, placeholders CinetPay/Moneroo/Flutterwave |
| `video_dedup.py` | SHA-256 hash anti-fraude : bloque le re-upload de la même vidéo par le même agent (si listing actif) |
| `listing_lifecycle.py` | Expiration listings (7 jours), traitement signalements, cleanup médias |
| `d7_verify.py` | D7VerifyClient — envoi/vérification OTP SMS |

---

# 6. Règles métier clés

## Visionnage (pay-per-view)
- 1 pack = 500 XOF = 33 clés virtuelles + 1 clé physique
- 1 vue = 1 clé virtuelle → 10 XOF agent + 5 XOF plateforme (atomique)
- UNIQUE(pack, video, user) = anti-double-crédit (revoir une vidéo = gratuit)

## Visite physique
- L'agent gagne 10 XOF **une seule fois par client par listing**
- Si le client n'a jamais vu de vidéo du listing → la visite consomme 1 clé virtuelle + 1 clé physique (10 XOF agent, 5 XOF plateforme)
- Si le client a déjà vu une vidéo du listing → la visite consomme uniquement la clé physique (0 XOF supplémentaire)
- Code de vérification : 5 caractères alphanumériques majuscules (ex: A3K7F)
- Annulation/expiration → clé physique restaurée, clé virtuelle jamais restaurée

## Anti-fraude vidéo
- Hash SHA-256 du fichier vidéo, comparé aux vidéos des listings **actifs** du même agent
- Un agent peut re-uploader une vidéo si son ancien listing est expiré/inactif

## Expiration des listings
- 7 jours après publication, le listing expire automatiquement (management command)
- L'agent peut renouveler avant expiration

## Wallet agent
- PIN de retrait hashé (make_password), 4 chiffres
- Seuil minimum de retrait : 2 000 XOF
- 1 seule demande PENDING à la fois
- Solde déduit immédiatement (anti-double-retrait)
- Approbation admin → payout via payment gateway

---

# 7. API — 47 endpoints

## Auth (11 endpoints)
```
POST /api/auth/register/client      Inscription client (→ OTP D7)
POST /api/auth/register/agent       Inscription agent (→ OTP D7)
POST /api/auth/login                Login → { access } + cookie refresh
POST /api/auth/refresh              Renouveler access (cookie)
POST /api/auth/logout               Logout + blacklist refresh
GET  /api/auth/me                   Profil courant
POST /api/auth/otp/request          Demander/relancer OTP
POST /api/auth/otp/verify           Vérifier OTP → créer compte
POST /api/auth/password/reset/request    Demander reset
POST /api/auth/password/reset/verify     Vérifier code reset
POST /api/auth/password/reset/finalize   Nouveau mot de passe
```

## Listings (11 endpoints)
```
GET  /api/listings/                         Recherche publique (filtres, pagination)
GET  /api/listings/{id}/                    Détail annonce
GET  /api/agent/listings/                   Mes annonces (agent)
POST /api/agent/listings/                   Créer annonce
GET/PUT/PATCH/DELETE /api/agent/listings/{id}/   CRUD annonce
POST /api/agent/listings/{id}/renew/        Renouveler (anti-expiration)
POST /api/agent/listings/{id}/images/       Upload image
DELETE /api/agent/listings/{id}/images/{pk}/ Supprimer image
POST /api/agent/listings/{id}/videos/       Upload vidéo (+ hash anti-fraude)
DELETE /api/agent/listings/{id}/videos/{pk}/ Supprimer vidéo
```

## Packs & Visionnage (5 endpoints)
```
GET  /api/client/packs/                     Mes packs
POST /api/client/packs/                     Acheter pack (dev simplifié, sans paiement)
GET  /api/client/packs/{id}/                Détail pack
POST /api/videos/{access_key}/watch/        Visionner vidéo (consomme 1 clé)
GET  /api/client/views/                     Historique visionnages
GET  /api/agent/views/                      Vues reçues (stats agent)
```

## Visites (8 endpoints)
```
GET/POST /api/client/visits/                Mes visites / Demander visite
POST     /api/client/visits/{id}/cancel/    Annuler visite
GET      /api/agent/visits/                 Visites reçues
POST     /api/agent/visits/{id}/confirm/    Confirmer visite
POST     /api/agent/visits/{id}/validate-code/  Valider code vérification
GET/POST /api/agent/availability/           Créneaux agent
GET/PUT/DELETE /api/agent/availability/{id}/  CRUD créneau
GET      /api/listings/{id}/availability/   Créneaux publics d'un listing
```

## Signalements (2 endpoints)
```
POST /api/listings/{id}/report/             Signaler un listing
GET  /api/client/reports/                   Mes signalements
```

## Wallet (6 endpoints)
```
GET  /api/agent/wallet/                     Solde + totaux
GET  /api/agent/wallet/entries/             Historique mouvements
POST /api/agent/wallet/set-pin/             Configurer PIN (1re fois)
POST /api/agent/wallet/change-pin/          Changer PIN
POST /api/agent/wallet/withdraw/            Demander retrait (PIN requis)
GET  /api/agent/wallet/withdrawals/         Historique retraits
```

## Client (8 endpoints)
```
GET       /api/client/dashboard/            Dashboard consolidé
GET/PATCH /api/client/profile/              Profil client
GET       /api/client/favorites/            Favoris
POST/DELETE /api/client/favorites/{id}/     Toggle favori
GET/POST  /api/client/saved-searches/       Recherches sauvegardées
GET/PUT/DELETE /api/client/saved-searches/{id}/  CRUD recherche
```

## Payments (4 endpoints) — NOUVEAU
```
POST /api/client/packs/buy/                 Initier achat (→ checkout_url provider)
POST /api/payments/webhook/                 Webhook provider (non auth)
POST /api/payments/simulate/{tx_ref}/confirm/  Simuler paiement (dev only)
GET  /api/client/payments/                  Historique paiements
```

---

# 8. Architecture Paiement (provider-agnostic)

## Flux Pay-in (Client → Plateforme)
1. Client `POST /api/client/packs/buy/` avec provider choisi
2. Backend crée `Payment(PENDING)` + appelle `gateway.create_checkout()`
3. Client redirigé vers page paiement du provider
4. Provider notifie `POST /api/payments/webhook/`
5. Backend vérifie via `gateway.verify_webhook()`, crée `PackPurchase`, `Payment(PAID)`

## Flux Payout (Plateforme → Agent)
1. Agent demande retrait (`POST /api/agent/wallet/withdraw/` + PIN)
2. `WithdrawalRequest(PENDING)` créé, solde déduit
3. Admin approuve → `approve_withdrawal()` appelle `gateway.create_payout()`
4. Mobile money transféré, `WithdrawalRequest(COMPLETED)`

## Gateways disponibles
- **SimulationGateway** (dev) : checkout_url local, confirmation manuelle, payout loggé
- **CinetPayGateway** : placeholder prêt (structure + __init__ avec clés)
- **MonerooGateway** : placeholder prêt
- **FlutterwaveGateway** : placeholder prêt

Config via `settings.py` :
```
PAYMENT_GATEWAY = env('PAYMENT_GATEWAY', default='simulation')
PAYMENT_CONFIG = { 'cinetpay': {...}, 'moneroo': {...}, 'flutterwave': {...} }
```

---

# 9. Sécurité

- JWT access court (10 min) en RAM, refresh long (14 jours) HttpOnly cookie
- OTP stateless via D7 Verify (pending_token signé)
- CORS avec credentials + origines explicites
- Origin/Referer check sur /auth/refresh et /auth/logout
- Passwords : make_password/check_password, StrongPasswordValidator
- PIN de retrait : hashé séparément du mot de passe
- Anti-fraude : UNIQUE(pack, video, user), video hash SHA-256, throttling
- select_for_update sur toutes les transactions financières
- CSP, HSTS, SSL configurables via .env

---

# 10. Management commands (tâches planifiées)

| Commande | Rôle |
|----------|------|
| `python manage.py expire_listings` | Expire les listings > 7 jours |
| `python manage.py auto_cancel_visits` | Annule les visites non confirmées (restore clé physique) |
| `python manage.py cleanup_media` | Supprime les fichiers médias des listings expirés |

Note : pas de Celery pour l'instant. Ces commandes peuvent être exécutées via cron ou Celery Beat en production.

---

# 11. Variables d'environnement (.env)

```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# D7 Verify (OTP SMS)
D7_API_BASE_URL=https://api.d7networks.com
D7_API_TOKEN=...
D7_ORIGINATOR=SignOTP

# Payment Gateway
PAYMENT_GATEWAY=simulation
# CINETPAY_API_KEY=...
# CINETPAY_SITE_ID=...
# CINETPAY_SECRET_KEY=...
# FLW_SECRET_KEY=...
# FLW_PUBLIC_KEY=...
# MONEROO_SECRET_KEY=...

# Cloudflare R2 (prod)
USE_R2=False
# R2_ACCESS_KEY_ID=...
# R2_SECRET_ACCESS_KEY=...
# R2_BUCKET_NAME=monajent-media
# R2_ENDPOINT_URL=...
```

---

# 12. État d'avancement — Backend

| Étape | Statut | Détail |
|-------|--------|--------|
| 1. Modèles + migrations | FAIT | 14 tables, 22 migrations, tous les index/contraintes |
| 2. Auth (inscription, login, OTP, reset) | FAIT | 11 endpoints, D7 Verify, JWT, stateless OTP |
| 3.1 Serializers + Vues Listings | FAIT | CRUD agent (9 endpoints), upload images/vidéos, hash anti-fraude |
| 3.2 Vues publiques Listings | FAIT | Recherche/filtrage, détail, pagination |
| 3.3 Serializers + Vues Packs | FAIT | Achat pack (dev), consommation clé, historique |
| 3.4 Service de visionnage | FAIT | Transaction atomique, 10 XOF agent + 5 XOF plateforme |
| 3.5 Vues Wallet | FAIT | Solde, historique, PIN, retrait, admin approbation |
| 3.6 Vues Visits | FAIT | Demande visite, créneaux, code vérif, confirm/cancel |
| 3.7 Client Profile + Favorites + SavedSearch | FAIT | Dashboard, profil, favoris, recherches sauvegardées |
| 3.8 Payments | FAIT | Architecture provider-agnostic, simulation, webhook, payout |
| **3.9 Frontend Dashboard Agent** | **A FAIRE** | Pages Vue.js : mes annonces, stats, wallet, visites |
| **3.10 Frontend Client** | **A FAIRE** | Pages Vue.js : recherche, visionnage, favoris, packs |

---

# 13. Ce qui reste à faire

## Backend (améliorations / prod-readiness)

1. **Implémenter un vrai gateway** : compléter CinetPayGateway ou MonerooGateway avec les clés API réelles (create_checkout, verify_webhook, create_payout)
2. **Celery / tâches async** : remplacer les management commands par des tâches Celery Beat pour expire_listings, auto_cancel_visits, cleanup_media
3. **Notifications** : push/SMS quand un paiement est confirmé, une visite est demandée/confirmée, un retrait est traité
4. **Tests unitaires** : aucun test écrit pour l'instant (tous les tests.py sont vides)
5. **Pagination globale** : configurer DEFAULT_PAGINATION_CLASS dans DRF
6. **Swagger/OpenAPI** : drf-spectacular est installé mais pas d'endpoint /api/docs/ configuré
7. **Admin avancé** : actions bulk, filtres avancés, tableaux de bord statistiques
8. **Logs/audit** : centraliser les logs de paiement, visionnage, retrait
9. **PostgreSQL** : migration vers Postgres pour la production
10. **Rate limiting avancé** : ajuster les throttles selon les retours d'usage

## Frontend (gros chantier — non commencé)

### 3.9 — Dashboard Agent (Vue.js)
- Mes annonces (CRUD, status, renouvellement)
- Stats (vues reçues, revenus par période, graphiques)
- Wallet (solde, historique, demande de retrait, gestion PIN)
- Visites (demandes reçues, créneaux, validation code)
- Profil agent (infos, KYC)

### 3.10 — Frontend Client (Vue.js)
- Recherche / exploration listings (filtres, carte)
- Visionnage vidéo (lecteur, consommation clé)
- Gestion packs (achat via paiement mobile, historique)
- Visites physiques (demande, suivi, code vérification)
- Favoris + recherches sauvegardées
- Dashboard / profil client

---

# 14. Fichiers clés (pour navigation rapide)

## Config
- `config/settings.py` — toute la configuration Django + JWT + CORS + Payment
- `apps/api/urls.py` — 47 routes REST

## Modèles
- `apps/users/models.py` — User, ClientProfile, AgentProfile
- `apps/listings/models.py` — Listing, Video, ListingImage, ListingReport
- `apps/packs/models.py` — PackPurchase, VirtualKeyUsage
- `apps/wallet/models.py` — Wallet, WalletEntry, PlatformRevenue, WithdrawalRequest
- `apps/visits/models.py` — AgentAvailabilitySlot, VisitRequest
- `apps/payments/models.py` — Payment
- `apps/favorites/models.py` — FavoriteListing, SavedSearch

## Services métier
- `apps/core/services/viewing.py` — consommation clé virtuelle (coeur business)
- `apps/core/services/visits.py` — visite physique (logique conditionnelle clé virtuelle)
- `apps/core/services/withdrawal.py` — retrait agent (PIN + payout gateway)
- `apps/core/services/payment.py` — initiation paiement + webhook
- `apps/core/services/payment_gateway.py` — interface abstraite + SimulationGateway
- `apps/core/services/video_dedup.py` — déduplication vidéo (SHA-256)
- `apps/core/services/listing_lifecycle.py` — expiration + signalements

## Auth
- `apps/api/views/auth.py` — toutes les vues auth
- `apps/api/serializers/auth.py` — serializers auth
- `apps/core/services/d7_verify.py` — intégration OTP D7

## Permissions & Throttles
- `apps/core/permissions.py` — 11 permissions métier
- `apps/api/throttles.py` — 8 throttles métier
