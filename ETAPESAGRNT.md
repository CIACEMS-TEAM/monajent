Voici le **bilan complet des fonctionnalités agent** :

---

## Bilan Agent — 12/12 fonctionnalités complètes

| # | Fonctionnalité | Statut | Notes |
|---|---|---|---|
| 1 | **Onboarding** (inscription, profil, coordonnées) | ✅ | 4 étapes, KYC optionnel |
| 2 | **KYC** (upload, soumission, review admin) | ✅ | Documents verrouillés après soumission |
| 3 | **Dashboard** (stats, cartes, top listings) | ✅ | Solde, vues, favoris, visites en attente |
| 4 | **Annonces** (CRUD, images, vidéos, conditions, GPS, partage) | ✅ | Anti-fraude vidéo SHA-256 + perceptuel |
| 5 | **Visites** (confirmation enrichie, code, NO_SHOW, annulation) | ✅ | Time-lock 15 min, meeting location, motifs |
| 6 | **Wallet** (solde, mouvements, filtres, retraits) | ✅ | Filtres source + type |
| 7 | **Analytics** (graphiques, tendances, conversion) | ✅ | Presets 7/14/28/90 jours |
| 8 | **Notifications** (liste, badge, polling, navigation clic) | ✅ | Liens vers page concernée |
| 9 | **Paramètres** (profil, sécurité, KYC, mot de passe, avatar) | ✅ | Eye toggle, PIN wallet |
| 10 | **Recherche** (desktop + mobile) | ✅ | Overlay mobile, filtre par titre/ville |
| 11 | **Lecteur vidéo sécurisé** (signed URL, thumbnail, anti-download) | ✅ | Token 1h, Content-Disposition |
| 12 | **Disponibilités** (créneaux récurrents + agenda ponctuel) | ✅ | CRUD + toggle actif |

## Ce qui reste en post-MVP (agent)

| Fonctionnalité | Statut |
|---|---|
| Notifications push/email/WebSocket | Reporté post-MVP |
| 2FA | Reporté post-MVP |
| Suppression de compte (RGPD) | Reporté post-MVP |
| Export CSV (analytics, wallet) | Reporté post-MVP |
| Date range wallet | Reporté post-MVP |

---

**Conclusion : le côté agent est complet pour le MVP.** Toutes les fonctionnalités essentielles sont en place (backend + frontend). On peut passer sereinement aux fonctionnalités client.




## CLIENT --------------------------------------------------------------------------------
Excellent, l'audit est terminé. Voici le bilan complet côté client :

---

## Bilan Client — Ce qui existe vs ce qui manque

### Ce qui est en place

| Module | Frontend | Backend | Statut |
|--------|----------|---------|--------|
| **Pages publiques** (accueil, grille annonces, détail annonce) | `HomePage.vue`, `HomeListings.vue`, `PublicListingView.vue` | API listings publiques | OK |
| **Profil client** (infos, avatar, édition) | `ClientProfile.vue` | `ClientProfileView` | OK |
| **Favoris** (liste) | `ClientFavorites.vue` | CRUD API favoris | Partiel |
| **Packs** (liste des packs achetés) | `ClientPacks.vue` | API packs | Partiel |
| **Visites** (liste, annulation, code vérif) | `ClientVisits.vue` | API visites | Partiel |
| **Historique vidéos** | `ClientHistory.vue` | API view history | OK |
| **Auth** (login, inscription client) | `LoginView`, `SignupClientView` | JWT, OTP | OK |

### Ce qui MANQUE pour le MVP client

| # | Fonctionnalité manquante | Impact | Effort |
|---|---|---|---|
| 1 | **Demande de visite depuis l'annonce** — le backend expose l'API + les disponibilités, mais aucun bouton ni formulaire sur `PublicListingView.vue` | **Critique** | Moyen |
| 2 | **Bouton favori sur l'annonce** — l'API toggle existe, mais pas de coeur/bouton sur la page détail ni sur les cards | **Important** | Petit |
| 3 | **Parcours achat de pack** — `InitiatePackPurchaseView` existe, mais pas de vrai checkout/paiement dans `ClientPacks.vue` | **Critique** | Moyen |
| 4 | **Signalement d'annonce** — `POST /api/listings/<id>/report/` existe, mais aucun bouton ou formulaire côté frontend | **Important** | Petit |
| 5 | **Dashboard client** — l'API `GET /api/client/dashboard/` existe, mais pas de page dashboard client | **Important** | Moyen |
| 6 | **Recherches sauvegardées** — CRUD API prêt, aucune UI | Nice-to-have | Petit |
| 7 | **Historique paiements** — `GET /api/client/payments/` existe, pas de page | **Important** | Petit |
| 8 | **Historique signalements** — `GET /api/client/reports/` existe, pas de page | Nice-to-have | Petit |
| 9 | **Store Pinia client dédié** — les vues appellent `http` directement au lieu d'un store centralisé | Qualité code | Moyen |

---

### Priorités recommandées pour le MVP

1. **Demande de visite** (sélecteur de créneau + formulaire sur la page annonce)
2. **Achat de pack** (checkout complet avec gateway paiement)
3. **Bouton favori** (coeur sur les cards + page détail)
4. **Signalement d'annonce** (bouton + modal sur la page détail)
5. **Dashboard client** (résumé : packs, visites, favoris)
6. **Historique paiements**
7. **Store client Pinia** (centralisation)




Voici le **bilan complet** de l'audit MonaJent.

---

## BILAN AUDIT TECHNIQUE MonaJent MVP

### Score global : **B / B+** (niveau intermédiaire-avancé, solide pour un MVP)

---

### CE QUI EST BIEN (niveau senior)

**1. Transactions DB / Race conditions (A-)**
- `transaction.atomic()` + `select_for_update()` sur **tous les flux critiques** : consommation de clés virtuelles, création de visites, retraits wallet, webhooks paiement
- `F()` expressions pour incréments atomiques (pas de `pack.virtual_used += 1`)
- Double-check `PENDING` dans le bloc atomique pour les webhooks (anti-race)
- `UNIQUE` constraint sur `VirtualKeyUsage` (anti-double consommation)

**2. Sécurité Auth (A-)**
- JWT hybride mature : access token Bearer (10 min), refresh HttpOnly cookie (14j, path restreint), rotation + blacklist
- `_is_same_site_request()` custom renforce la protection CSRF sur refresh/logout
- `StrongPasswordValidator` custom (3 classes sur 4 requises)
- Login lockout (5 fails = 15 min blocage via cache)
- Vidéos protégées par token signé avec expiration

**3. Permissions (A)**
- 12+ classes de permissions custom (`IsAgent`, `IsClient`, `IsListingOwner`, `IsWalletOwner`, etc.)
- Object-level permissions sur toutes les ressources sensibles
- Séparation URL `agent/` vs `client/` avec permissions appropriées

**4. Rate Limiting (A)**
- DRF `ScopedRateThrottle` avec 15+ rates custom par feature (auth 5/min, OTP 3/min, etc.)
- Throttle classes custom par criticité

**5. Architecture (B+)**
- 9 modules dans `core/services/` pour la logique métier
- Gateway pattern pour paiements multi-provider
- Monolithe modulaire (10 apps Django bien découpées)
- Docker multi-stage, entrypoint.sh mature, Celery Beat séparé

---

### CE QUI EST SUFFISANT POUR LE MVP (mais à améliorer)

**6. Celery (B)**
- Tasks avec `bind=True`, `max_retries`, `self.retry(exc=exc)` — pattern correct
- Beat avec 3 tâches planifiées (expire listings, auto-cancel visits, cleanup media)
- `CELERY_TASK_ALWAYS_EAGER` pour dev local — bien pensé

**7. ORM (B+)**
- `select_related` / `prefetch_related` sur les hot paths (listings, visits, payments)
- `annotate()` pour analytics et bulk operations
- Quelques `sum()` en Python qui devraient etre `aggregate()` dans la DB

**8. Design Patterns (B+)**
- Service layer séparé des views pour les flux argent
- Pas de over-engineering (pas de DDD complet — correct pour un MVP Django)

---

### CE QUI MANQUE ET DOIT ETRE FAIT (priorité MVP)

| Priorité | Item | Impact |
|----------|------|--------|
| **CRITIQUE** | `_client_ip()` non importé dans `auth.py` (NameError au OTPVerify) | **Bug bloquant** : crash au moment de la vérification OTP si l'utilisateur a accepté les CGU |
| **CRITIQUE** | `PasswordChangeView` bypass `StrongPasswordValidator` (vérifie juste `len >= 8`) | Faille sécurité : mots de passe faibles acceptés au changement |
| **HAUTE** | Pagination absente sur toutes les listes (visits, tickets, notifications, payments) | Performance qui dégradent avec la croissance des données |
| **HAUTE** | Sentry non intégré (DSN prévu mais SDK pas installé) | Zero visibilité sur les erreurs en production |
| **HAUTE** | Webhook Paystack skip la vérification HMAC si body/signature absent | Faille sécurité paiement |
| **MOYENNE** | `send_ticket_reply_email.delay()` jamais appelé | Feature support email non fonctionnelle |
| **MOYENNE** | `generate_video_thumbnail_task` jamais enqueued (synchrone) | Thumbnail bloque la requête upload |
| **MOYENNE** | `select_for_update()` hors `atomic()` dans `process_webhook` (1ere query) | Lock non garanti techniquement |

---

### CE QUI RESTE POUR LE NIVEAU SENIOR (post-MVP)

| Domaine | A faire |
|---------|---------|
| **Tests** | **0% couverture actuellement.** pytest + tests unitaires services critiques (payment, viewing, withdrawal) + tests API integration |
| **Cache applicatif** | `cache_page` sur listings publics, cache dashboard analytics, invalidation on update |
| **Queue management** | Queues nommées (email/high, maintenance/low), workers dédiés |
| **Idempotence avancée** | Idempotency keys pour emails, distributed lock sur tasks Beat (celery-once ou Redis lock) |
| **CI/CD** | GitHub Actions (lint, tests, build Docker, push registry) |
| **Logging structuré** | JSON logging pour ELK/Loki, Sentry Celery integration |
| **Monitoring** | Flower pour Celery, healthcheck endpoint `/api/health/`, Prometheus metrics |
| **Documentation** | Swagger UI via drf-spectacular, ADR (Architecture Decision Records) |
| **Code quality** | ruff + black + isort + pre-commit hooks, type hints complets |
| **Notifications** | Extraire un `NotificationService` (actuellement inline dans 5+ views) |

---

Le `checklist_data.json` a été mis à jour avec les notes détaillées pour chaque item. Les 3 bugs critiques (import `_client_ip`, `PasswordChangeView` faible, webhook HMAC) et la pagination sont les priorités immédiates avant tout lancement. Est-ce qu'on s'attaque aux corrections ?