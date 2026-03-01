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
