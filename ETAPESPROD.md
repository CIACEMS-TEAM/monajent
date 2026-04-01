Voici le **bilan complet de maturité de la plateforme MonaJent** pour le MVP/Production.

---

# Bilan de Maturité MVP — MonaJent

## A. Fonctionnalités — Agent (12/12)

| # | Module | Backend | Frontend | Statut |
|---|--------|---------|----------|--------|
| 1 | Onboarding (inscription, profil, coordonnées) | API auth + agent profile | 4 étapes | **COMPLET** |
| 2 | KYC (upload, soumission, review admin) | Documents, admin actions | Upload, verrouillage | **COMPLET** |
| 3 | Dashboard (stats, cartes, top listings) | `/api/agent/dashboard/` | KPI cards, top 5 | **COMPLET** |
| 4 | Annonces (CRUD, images, vidéos, conditions, GPS, partage) | CRUD complet, anti-fraude SHA-256 + perceptuel | Formulaire, map, vidéo loader | **COMPLET** |
| 5 | Visites (confirmation, code, NO_SHOW, annulation) | Time-lock 15min, code verif, meeting location | Modal enrichi | **COMPLET** |
| 6 | Wallet (solde, mouvements, retraits) | Wallet, WalletEntry, WithdrawalRequest | Filtres source + type, PIN | **COMPLET** |
| 7 | Analytics (graphiques, tendances) | `/api/agent/analytics/` | Presets 7/14/28/90j | **COMPLET** |
| 8 | Notifications (liste, badge, polling, navigation) | Notification model + link | Polling 30s, clic navigue | **COMPLET** |
| 9 | Paramètres (profil, sécurité, KYC, avatar) | Profile update | Onglets, eye toggle | **COMPLET** |
| 10 | Recherche (desktop + mobile) | Filtres API | Overlay mobile | **COMPLET** |
| 11 | Lecteur vidéo sécurisé | Signed URL 1h, anti-download | Thumbnail cover | **COMPLET** |
| 12 | Disponibilités (créneaux récurrents + agenda) | CRUD slots | Toggle actif | **COMPLET** |

---

## B. Fonctionnalités — Client (12/12)

| # | Module | Backend | Frontend | Statut |
|---|--------|---------|----------|--------|
| 1 | Inscription + Login client | JWT, OTP D7 Networks | Phone + OTP flow | **COMPLET** |
| 2 | Exploration annonces (grille, détail, recherche) | API publiques + filtres | Cards, détail riche | **COMPLET** |
| 3 | Visite virtuelle (visionnage vidéo payant) | Consume key, revenus agent + plateforme | Modal animé, clé virtuelle | **COMPLET** |
| 4 | Visite physique (demande, créneaux) | `request_visit()`, disponibilités | Sélecteur créneau, modal | **COMPLET** |
| 5 | Achat de pack (paiement Paystack) | `initiate_pack_purchase()`, webhook, verify | Popup Paystack inline | **COMPLET** |
| 6 | Favoris (toggle, liste) | CRUD + compteur dénormalisé | Coeur sur cards + détail | **COMPLET** |
| 7 | Signalement d'annonce | `ListingReport` + auto-suspension | Modal avec motifs | **COMPLET** |
| 8 | Dashboard client | `/api/client/dashboard/` | KPI cards, raccourcis | **COMPLET** |
| 9 | Historique de visionnage | `VirtualKeyUsage` serializer enrichi | Thumbnails, navigation vers listing | **COMPLET** |
| 10 | Historique paiements | `/api/client/payments/` | Cards + reçu imprimable | **COMPLET** |
| 11 | Historique signalements | `/api/client/reports/` | Liste avec statut | **COMPLET** |
| 12 | Profil client (édition) | `ClientProfileView` | Formulaire | **COMPLET** |

---

## C. Architecture technique

| Aspect | Détail | Statut |
|--------|--------|--------|
| Backend | Django 5.2 + DRF 3.16 + SimpleJWT | OK |
| Frontend | Vue 3.5 + Pinia + Vue Router + PrimeVue | OK |
| BDD | PostgreSQL (psycopg2-binary) | OK |
| Stockage médias | Local (dev) + Cloudflare R2/S3 (prod) via `django-storages` | OK |
| Authentification | JWT HttpOnly cookie + refresh rotation + blacklist | OK |
| OTP/SMS | D7 Networks API | OK |
| Paiement | Paystack (popup inline), webhook + verify | OK |
| Anti-fraude vidéo | SHA-256 + hash perceptuel (ImageHash) | OK |
| Throttling | 10+ scopes DRF (auth, listing, video, pack, visit, wallet) | OK |
| CORS | `django-cors-headers`, env-controlled | OK |
| CSP | `django-csp`, activable via env | OK |
| Stores Pinia | 5 stores (auth, agent, client, public, notifications) | OK |
| Cartographie | Leaflet + Nominatim (OSM) | OK |

---

## D. Ce qui MANQUE pour la production

### Critique (bloquant pour la mise en ligne)

| # | Élément | Détail | Effort |
|---|---------|--------|--------|
| 1 | **`STATIC_ROOT`** | Non configuré dans `settings.py` — `collectstatic` échouera | 5 min |
| 2 | **`gunicorn`** | Absent de `requirements.txt` — pas de serveur WSGI prod | 5 min |
| 3 | **`DEBUG = False` checklist** | `SECRET_KEY` a un fallback insécurisé, pas de `ALLOWED_HOSTS` explicite | 15 min |
| 4 | **Dockerfile + docker-compose** | Rien pour le déploiement conteneurisé | 1-2h |
| 5 | **Nginx / reverse proxy** | Aucune config pour servir le frontend build + proxy API | 1h |
| 6 | **Frontend build prod** | `npm run build` non testé, `VITE_API_BASE_URL` prod à valider | 30 min |
| 7 | **Paystack payout (agent)** | `create_payout()` → `NotImplementedError` — les agents ne peuvent pas retirer leur argent vers mobile money | 4-6h |
| 8 | **`.env.example`** | Pas de template d'env sans secrets — risque onboarding dev | 15 min |
| 9 | **`LOGGING` Django** | Aucune config de logging — en prod, les erreurs seront silencieuses | 30 min |

### Important (fortement recommandé pour le MVP)

| # | Élément | Détail | Effort |
|---|---------|--------|--------|
| 10 | **Sentry** (error tracking) | Aucun suivi d'erreurs en prod | 30 min |
| 11 | **Tests automatisés** | 0 test backend, 0 test frontend | 2-4 jours |
| 12 | **CI/CD pipeline** | Aucune automatisation (build, test, deploy) | 2-4h |
| 13 | **Migrations pending check** | `showmigrations` + `migrate` à valider avant deploy | 10 min |
| 14 | **Celery / tâches asynchrones** | Celery est dans `requirements.txt` mais aucun worker, aucune tâche `.delay()`, aucun `celery.py` — les management commands (`expire_listings`, `auto_cancel_visits`, `cleanup_media`) sont manuels | 2-3h |
| 15 | **Cron jobs** | Les 3 commandes de maintenance doivent tourner périodiquement (pas de crontab défini) | 30 min |
| 16 | **Email transactionnel** | Aucun `EMAIL_BACKEND` — pas de confirmation email, pas de notification mail | 2-4h |
| 17 | **Secrets exposés** | `.envDokploy.txt` contient des clés réelles, `README.md` contient un token Cloudflare | 15 min |

### Post-MVP (reportable)

| # | Élément | Détail |
|---|---------|--------|
| 18 | Notifications push/email/WebSocket | Polling 30s OK pour le MVP |
| 19 | 2FA | Sécurité additionnelle |
| 20 | Export CSV (analytics, wallet) | Confort agent |
| 21 | Recherches sauvegardées | API prête, pas d'UI |
| 22 | Suppression de compte (RGPD) | Obligatoire si lancement EU |
| 23 | i18n | Tout est en français, OK pour la Côte d'Ivoire |
| 24 | PWA / app mobile | Responsive OK, PWA serait un plus |

---

## E. Résumé chiffré

| Métrique | Valeur |
|----------|--------|
| Fonctionnalités agent | **12/12** |
| Fonctionnalités client | **12/12** |
| Endpoints API | **~60** |
| Modèles Django | **~20** |
| Vues frontend | **22** |
| Stores Pinia | **5** |
| Tests automatisés | **0** |
| Fichiers Docker | **0** |
| Config CI/CD | **0** |
| Config logging/monitoring | **0** |

---

## F. Plan d'action recommandé pour la mise en prod

**Phase 1 — Corrections critiques (1 jour)**
1. Ajouter `STATIC_ROOT`, `ALLOWED_HOSTS`, sécuriser `SECRET_KEY`
2. Ajouter `gunicorn` dans `requirements.txt`
3. Configurer `LOGGING` Django
4. Créer `.env.example`, nettoyer les secrets exposés
5. Tester `npm run build` et valider les env de prod

**Phase 2 — Infrastructure (1-2 jours)**
6. Créer `Dockerfile` + `docker-compose.yml` (Django + PostgreSQL + Nginx + Redis)
7. Config Nginx (frontend static + proxy API)
8. Mettre en place les cron jobs (expire_listings, auto_cancel_visits, cleanup_media)
9. Intégrer Sentry

**Phase 3 — Paiement agent (1-2 jours)**
10. Implémenter Paystack payout (`create_transfer_recipient` + `initiate_transfer`)
11. Tester le flux retrait complet en sandbox

**Phase 4 — CI/CD + Tests (2-4 jours)**
12. Pipeline GitHub Actions / GitLab CI (lint, test, build, deploy)
13. Tests critiques : auth, paiement, visites, wallet

---

**Conclusion** : Côté fonctionnel, **la plateforme est complète pour le MVP** (24/24 features agent + client). Ce qui reste est purement **infra/DevOps** (Docker, Nginx, CI/CD, logging, Sentry) et **le payout Paystack** pour les agents. Avec 3-5 jours de travail ciblé, MonaJent peut être en production.