# Contexte session — MonaJent : IA, OG Share, Recherche, UX Mobile, PWA
## Dernière mise à jour : 8 avril 2026 (session 3)

Ce document résume TOUT ce qui a été réalisé dans les sessions de travail. Il sert de contexte pour un LLM reprenant le travail.

### Sessions
- **Session 1** (7 avril 2026) : Refactorisation IA Strategy Pattern + OG Share v1 + Pitch business
- **Session 2** (8 avril 2026) : Fix WhatsApp OG v2 + Fix recherche IA + Analyse TikTok
- **Session 3** (8 avril 2026) : Responsivité mobile, assistants vocaux Mona, onboarding, PWA

---

## 1. Refactorisation du service IA — Strategy Pattern (TERMINÉ)

### Problème initial
Le fichier `apps/core/services/gemini_ai.py` était un monolithe de 320 lignes contenant :
- Les exceptions
- Le parsing JSON
- Les prompts
- Les providers Groq et Gemini (fonctions inline)
- L'orchestrateur multi-providers

Ajouter un nouveau provider IA nécessitait de modifier l'orchestrateur existant → violation du principe Open/Closed (SOLID).

### Solution implémentée — Strategy Pattern léger

Nouvelle architecture dans `apps/core/services/ai/` :

```
apps/core/services/
├── ai/
│   ├── __init__.py          # API publique + orchestrateur (import depuis ici)
│   ├── _registry.py         # Protocol + registre auto-discovery des providers
│   ├── _prompts.py          # Prompts métier séparés (extraction annonce + recherche)
│   ├── _parsing.py          # Parsing JSON commun (strip fences, validation)
│   ├── exceptions.py        # AIConfigurationError, AIParseError, AIProviderError + aliases rétro-compatibles
│   └── providers/
│       ├── __init__.py      # Auto-discovery via pkgutil.iter_modules()
│       ├── groq.py          # Provider Groq — priorité 10 (primaire, 1000 RPD gratuit)
│       ├── deepseek.py      # Provider DeepSeek — priorité 50 (secondaire, ~0.28$/M tokens)
│       └── gemini.py        # Provider Gemini — priorité 90 (fallback, 20 RPD free tier)
├── gemini_ai.py             # Shim rétro-compatible (re-export vers ai/)
```

### Comment ça fonctionne

1. **Chaque provider** s'auto-enregistre via `register_provider(name, priority, is_available, generate)` au moment de l'import.
2. **L'auto-discovery** dans `providers/__init__.py` importe automatiquement tous les modules du package via `pkgutil.iter_modules()`.
3. **L'orchestrateur** dans `ai/__init__.py` → `_generate_text(prompt)` essaie chaque provider par ordre de priorité (plus bas = essayé en premier). Si un provider échoue, il passe au suivant.
4. **Rétro-compatibilité** : Le fichier `gemini_ai.py` est un shim qui re-exporte tout depuis `ai/`. Les imports existants (`from apps.core.services.gemini_ai import ...`) continuent de fonctionner.

### Pour ajouter un nouveau provider (ex: Mistral, OpenRouter)

Créer UN SEUL fichier `providers/mistral.py` :
```python
from django.conf import settings
from .._registry import register_provider

def _is_available() -> bool:
    return bool((getattr(settings, 'MISTRAL_API_KEY', None) or '').strip())

def _generate(prompt: str) -> str:
    # ... appel API ...
    return response_text

register_provider(name='mistral', priority=40, is_available=_is_available, generate=_generate)
```
Aucun autre fichier à modifier.

### Providers configurés

| Priorité | Provider | SDK | Modèle | Quota gratuit | Variable .env |
|----------|----------|-----|--------|---------------|---------------|
| 10 | **Groq** | `openai` (compatible) | `llama-3.3-70b-versatile` | 1000 req/jour | `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_API_URL` |
| 50 | **DeepSeek** | `openai` (compatible) | `deepseek-chat` (V3.2) | Pas de rate limit (~0.28$/M tokens) | `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_API_URL` |
| 90 | **Gemini** | `google-genai` | `gemini-3-flash-preview` | 20 req/jour | `GEMINI_API_KEY`, `GEMINI_MODEL` |

### Variables ajoutées dans settings.py

```python
# ── AI Providers ─────────────────────────────────────────────────────────────
# Groq (primaire — 1000 RPD gratuit, ultra-rapide)
GROQ_API_KEY = env('GROQ_API_KEY', default='')
GROQ_MODEL = env('GROQ_MODEL', default='llama-3.3-70b-versatile')
GROQ_API_URL = env('GROQ_API_URL', default='https://api.groq.com/openai/v1')
# DeepSeek (secondaire — pas de rate limit, ~0.28$/M tokens)
DEEPSEEK_API_KEY = env('DEEPSEEK_API_KEY', default='')
DEEPSEEK_MODEL = env('DEEPSEEK_MODEL', default='deepseek-chat')
DEEPSEEK_API_URL = env('DEEPSEEK_API_URL', default='https://api.deepseek.com')
# Gemini (fallback — 20 RPD free tier)
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
GEMINI_MODEL = env('GEMINI_MODEL', default='gemini-3-flash-preview')
```

### Vue DRF mise à jour (`apps/api/views/ai.py`)

- Import direct depuis `apps.core.services.ai` au lieu de `gemini_ai`
- Check de disponibilité via `_any_provider_available()` qui consulte le registre (plus de dépendance sur `GEMINI_API_KEY` uniquement)
- Fonctions publiques importées directement : `extract_listing_from_text`, `parse_search_intent`

### Tests passés
- 4 tests unitaires Django existants (`test_gemini_ai.py`) passent via le shim rétro-compatible
- Vérification d'import, d'alias d'exceptions, d'enregistrement des 3 providers, de l'ordre de priorité

---

## 2. Amélioration du système de partage social OG (TERMINÉ)

### Problème
Les aperçus enrichis (rich previews) sur WhatsApp ne montraient plus les images des annonces. Facebook fonctionnait. Causes :
1. Les URLs d'images R2 en prod utilisent des **signed URLs** (`?X-Amz-Signature=...`) qui expirent après 1 heure
2. WhatsApp est très strict : timeout court, pas de redirect, URLs propres requises
3. En dev, `request.build_absolute_uri()` génère des URLs `localhost:8000` inaccessibles par les bots

### Solution — Proxy image stable

Ajout d'un endpoint **proxy image** qui sert directement les octets du fichier :

```
GET /api/share/<slug>/image.jpg  →  Sert l'image JPEG directement (200 OK, image/jpeg)
```

L'URL `og:image` pointe maintenant vers ce proxy au lieu de la signed URL R2 :
```
Avant : https://bucket.r2.cloudflarestorage.com/thumb.jpg?X-Amz-Signature=...&Expires=3600
Après : https://api.monajent.com/api/share/mon-annonce/image.jpg
```

### Fichiers modifiés

**`apps/api/views/share.py`** — Refonte complète :
- `ListingShareOGView` : Page OG enrichie avec tous les tags
- `ListingShareImageView` (NOUVEAU) : Proxy image stable avec cache 24h
- `_og_image_url()` : Construit l'URL proxy au lieu de l'URL R2 signée
- `_get_listing_image_field()` : Priorité image > thumbnail vidéo > fallback
- `_fallback_image_url()` : Logo MonaJent (`/og-default.png`)
- BOT_PATTERN étendu : ajout `TikTok`, `Bytespider`

**`apps/api/urls.py`** :
- Ajout route `path('share/<slug:slug>/image.jpg', ListingShareImageView.as_view())`

**`frontend/public/og-default.png`** (NOUVEAU) :
- Image de fallback (logo MonaJent) pour les annonces sans photo/thumbnail

**`config/settings.py`** :
- Ajout `BACKEND_BASE_URL = env('BACKEND_BASE_URL', default='')` pour construire les URLs absolues

**`.env`** :
- Ajout `BACKEND_BASE_URL=http://localhost:8000` (en prod : `https://api.monajent.com`)

### Tags OG ajoutés/améliorés

| Tag | Avant | Après |
|-----|-------|-------|
| `og:image` | URL R2 signée (expire) | URL proxy stable (`/api/share/<slug>/image.jpg`) |
| `og:image:type` | Absent | `image/jpeg` |
| `og:site_name` | `MonaJent` | `MonaJent — Immobilier Côte d'Ivoire` |
| `article:author` | Absent | Nom de l'agence ou de l'agent |
| `product:price:amount` | Absent | Prix en XOF (pour Facebook Marketplace) |
| `product:price:currency` | Absent | `XOF` |
| `twitter:image:alt` | Absent | Titre + MonaJent |
| `link rel=canonical` | Absent | URL canonique |
| Fallback image | Aucune (aperçu vide) | Logo MonaJent |
| Description | Basique | Enrichie (ameublement, conditions) |

### Pour la production
Ajouter dans le `.env` Docker/Dokploy :
```
BACKEND_BASE_URL=https://api.monajent.com
```

### Note sur le cache WhatsApp
WhatsApp cache les aperçus de liens pendant **jusqu'à 7 jours**. Pour les liens déjà partagés avant ce fix, il faut attendre l'expiration du cache ou partager un lien d'annonce jamais partagé auparavant.

---

## 2b. Fix WhatsApp OG — Corrections supplémentaires (8 avril 2026)

### Problèmes diagnostiqués

5 causes identifiées pour les aperçus WhatsApp incohérents :

| # | Problème | Sévérité | Corrigeable ? |
|---|----------|----------|---------------|
| 1 | **Multi-contacts WhatsApp** : quand on envoie à plusieurs contacts via `wa.me/?text=...`, WhatsApp ne génère PAS d'aperçu riche | HAUTE | NON (limitation WhatsApp) |
| 2 | **Image proxy retourne 302** pour le fallback → WhatsApp ne suit pas les redirections pour `og:image` + le fichier `og-default.png` n'existait pas → 302 → 404 | CRITIQUE | OUI ✓ |
| 3 | **Pas de Content-Length** : `FileResponse` streaming depuis R2 n'envoie pas Content-Length, les bots WhatsApp en ont besoin | HAUTE | OUI ✓ |
| 4 | **og:image:type hardcodé** en `image/jpeg` même quand l'image est PNG/WebP | MOYENNE | OUI ✓ |
| 5 | **Nginx intercepte `/share/*/image.jpg`** : la location regex `~* \.(jpg)$` a priorité sur le prefix `/share/` → les requêtes image OG sont traitées comme fichiers statiques (→ 404) au lieu d'être proxiées | CRITIQUE | OUI ✓ |

### Corrections appliquées

**`apps/api/views/share.py`** — Refonte du proxy image :
- Image lue en mémoire → `HttpResponse` avec `Content-Length` exact
- Fallback : image 1200x630 générée via Pillow (fond vert + texte "MonaJent"), servie directement en 200 (plus de 302)
- `og:image:type` dynamique basé sur le type réel du fichier
- `og:image` URL utilise `FRONTEND_URL` au lieu de `BACKEND_BASE_URL` → même domaine que `og:url`

**`frontend/nginx.conf`** :
- Location `/share/` changée de prefix simple à `^~` (stops regex matching) → empêche la location `~* \.(jpg)$` d'intercepter `/share/*/image.jpg`

**`ShareDialog.vue`** (partage agent) :
- URL mise sur sa propre ligne (suppression du préfixe "Voir l'annonce :") pour une meilleure détection d'URL par WhatsApp
- Ajout d'un indice UX : "Pour que l'aperçu avec image s'affiche sur WhatsApp, envoyez à un seul contact à la fois"

**`PublicListingView.vue`** (partage public) :
- Texte de partage enrichi : ajout du type (Location/Vente), quartier
- URL sur sa propre ligne

### IMPORTANT — Limitation WhatsApp multi-contacts
Quand un utilisateur partage via `wa.me/?text=...` et sélectionne **plusieurs contacts**, WhatsApp envoie le texte brut sans jamais récupérer les métadonnées OG. C'est par conception (WhatsApp fait un "broadcast" au lieu de composer dans chaque chat). **Rien à faire côté serveur**. L'indice UX dans ShareDialog informe l'utilisateur.

---

## 3. Document de pitch & business model (TERMINÉ)

### Fichier créé : `PITCH_MONAJENT.md`

Document stratégique exhaustif (588 lignes) couvrant :
1. **Pitch** repositionné
2. **Contexte** du marché immobilier ivoirien
3. **Problèmes** identifiés (clients, agents, marché)
4. **Solution** MonaJent
5. **Le lien partageable** comme moteur de croissance
6. **Fonctionnalités** clés
7. **Personas** détaillés (agent indépendant, agent agence, locataire, acheteur)
8. **Valeurs ajoutées** pour chaque partie
9. **Analyse concurrentielle**
10. **Freins à l'adoption** et solutions
11. **6 modèles de monétisation** avec stratégie par phases
12. **Recommandations** stratégiques court/moyen/long terme
13. **KPIs** à suivre

### Repositionnement stratégique clé

L'insight majeur de cette session est le **repositionnement du pitch** :

**AVANT** (marketplace classique) :
> "Venez publier vos annonces sur MonaJent"
→ Demande à l'agent de changer de comportement
→ En concurrence avec WhatsApp/Facebook
→ Problème poule-et-œuf

**APRÈS** (outil + lien partageable) :
> "Publie une fois, partage partout. Gagne de l'argent à chaque clic."
→ L'agent garde ses habitudes (WhatsApp, Facebook)
→ MonaJent est COMPLÉMENTAIRE aux réseaux sociaux
→ Chaque agent est un canal de distribution gratuit
→ Pas de problème poule-et-œuf

Le **lien partageable** (`monajent.com/share/<slug>/`) avec aperçu riche est le moteur de croissance à coût zéro : chaque fois qu'un agent partage dans un groupe WhatsApp (500+ membres), c'est du marketing gratuit.

---

## 4. Logs Groq — RemoteProtocolError (PAS un bug)

Les logs Django montrent des erreurs `Server disconnected without sending a response` quand Groq coupe la connexion. C'est **normal et géré** :
1. Le SDK OpenAI a un mécanisme de retry intégré (2 retries avec backoff)
2. La deuxième tentative réussit systématiquement (200 OK)
3. L'utilisateur ne voit aucune erreur
4. En `DEBUG`, ces logs sont verbeux mais inoffensifs

Pour réduire le bruit en prod : passer le log level httpx/httpcore à `WARNING`.

---

## 5. État actuel des fichiers clés

### Backend — Fichiers créés/modifiés (toutes sessions)

| Fichier | Session | Action |
|---------|---------|--------|
| `apps/core/services/ai/__init__.py` | S1+S2 | CRÉÉ — API publique + orchestrateur + `_broaden_location_filters()` |
| `apps/core/services/ai/_registry.py` | S1 | CRÉÉ — Protocol + registre auto-discovery |
| `apps/core/services/ai/_prompts.py` | S1+S2 | CRÉÉ — Prompts extraction annonce + recherche (SEARCH_INTENT_PROMPT refait en S2) |
| `apps/core/services/ai/_parsing.py` | S1 | CRÉÉ — Parsing JSON commun |
| `apps/core/services/ai/exceptions.py` | S1 | CRÉÉ — Exceptions + aliases rétro-compatibles |
| `apps/core/services/ai/providers/__init__.py` | S1 | CRÉÉ — Auto-discovery pkgutil |
| `apps/core/services/ai/providers/groq.py` | S1 | CRÉÉ — Provider Groq (priorité 10) |
| `apps/core/services/ai/providers/deepseek.py` | S1 | CRÉÉ — Provider DeepSeek (priorité 50) |
| `apps/core/services/ai/providers/gemini.py` | S1 | CRÉÉ — Provider Gemini (priorité 90) |
| `apps/core/services/gemini_ai.py` | S1 | MODIFIÉ — Remplacé par shim rétro-compatible (21 lignes) |
| `apps/api/views/ai.py` | S1 | MODIFIÉ — Imports depuis ai/, check _any_provider_available() |
| `apps/api/views/share.py` | S1+S2 | MODIFIÉ — Refonte OG + proxy image en mémoire + fallback Pillow + og:image:type dynamique |
| `apps/api/views/listings.py` | S2 | MODIFIÉ — `address` ajouté aux `search_fields` |
| `apps/api/urls.py` | S1 | MODIFIÉ — Ajout route image.jpg |
| `config/settings.py` | S1 | MODIFIÉ — DEEPSEEK_*, BACKEND_BASE_URL |

### Frontend — Fichiers créés/modifiés

| Fichier | Session | Action |
|---------|---------|--------|
| `frontend/nginx.conf` | S2 | MODIFIÉ — `^~` pour `/share/` (empêche interception .jpg par regex) |
| `frontend/src/components/AgentsComponents/Listings/ShareDialog.vue` | S2 | MODIFIÉ — URL sur propre ligne + hint multi-contact WhatsApp |
| `frontend/src/views/public/PublicListingView.vue` | S2+S3 | MODIFIÉ — shareText enrichi (S2) + layout mobile suggestions en dessous + padding (S3) |
| `frontend/index.html` | S3 | MODIFIÉ — Meta PWA, manifest link, apple-touch-icon, enregistrement SW |
| `frontend/src/views/HomePage.vue` | S3 | MODIFIÉ — Import MonaSearch/OnboardingTour/PwaInstallPrompt, data-tour attrs, onboarding logic, activeBottomTab, handleBottomNavProfile mobile |
| `frontend/src/views/client/ClientDashboard.vue` | S3 | MODIFIÉ — Liens rapides, déconnexion, avatar profil, grille responsive |
| `frontend/src/components/WelcomeOverlay.vue` | S3 | MODIFIÉ — Émet `closed` pour déclencher l'onboarding |
| `frontend/src/components/MonaSearch.vue` | S3 | CRÉÉ — Recherche vocale IA client (FAB + panel + invite bubble + son 30s) |
| `frontend/src/components/MonaAssistant.vue` | S3 | CRÉÉ — Saisie vocale IA agent (FAB + panel + greeting adaptatif) |
| `frontend/src/components/OnboardingTour.vue` | S3 | CRÉÉ — Tour guidé 4 étapes (spotlight adaptatif desktop/mobile) |
| `frontend/src/components/PwaInstallPrompt.vue` | S3 | CRÉÉ — Banner d'installation PWA (Android + iOS) |
| `frontend/public/manifest.webmanifest` | S3 | CRÉÉ — Manifeste PWA (standalone, portrait, shortcuts) |
| `frontend/public/sw.js` | S3 | CRÉÉ — Service Worker (cache-first assets, network-first pages) |
| `frontend/public/pwa-icon-*.png` | S3 | CRÉÉ — 8 icônes PWA (72→512) + 1 maskable + 1 apple-touch-icon |
| `frontend/src/assets/media/discord-sounds.mp3` | S3 | CRÉÉ — Son notification pour la bulle d'invitation Mona |

### Racine — Fichiers créés

| Fichier | Session | Action |
|---------|---------|--------|
| `PITCH_MONAJENT.md` | S1 | CRÉÉ — Pitch + business model (588 lignes) |
| `CONTEXTE_SESSION_IA.md` | S1+S2+S3 | CRÉÉ puis mis à jour — Ce fichier |
| `search_tiktokshare.md` | S2 | CRÉÉ — Rapport deep research Gemini sur TikTok (rejeté) |

### .env — Variables ajoutées

```dotenv
# DeepSeek
DEEPSEEK_API_KEY=sk-0834649846734d54b70c739817697f33
DEEPSEEK_API_KEY_NAME=mj-api-dps
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/v1

# Backend base URL (pour OG images)
BACKEND_BASE_URL=http://localhost:8000
# En prod : BACKEND_BASE_URL=https://api.monajent.com
```

---

## 2c. Fix Recherche IA — Résultats manquants (8 avril 2026)

### Problème
La recherche via l'assistant Mona ne trouvait pas certaines annonces existantes. Par exemple, un bien à "Cocody Angré 9ème Tranche" n'était pas trouvé en cherchant "Angré".

### Causes racines

| # | Problème | Impact |
|---|----------|--------|
| 1 | **`search_fields` incomplet** : le champ `address` manquait → la recherche textuelle ne cherchait pas dans l'adresse | HAUTE |
| 2 | **L'IA utilisait des filtres exacts** (`city=Abidjan`, `neighborhood=Cocody`) au lieu du paramètre `search` qui fait du `icontains` sur 5 champs | CRITIQUE |
| 3 | **Le prompt IA pas assez directif** : il laissait l'IA choisir entre filtres exacts et `search`, et l'IA choisissait souvent les filtres stricts | HAUTE |

### Comment la recherche fonctionne (après fix)

1. L'utilisateur dit : "Je cherche un 3 pièces à Angré budget 300k"
2. L'IA retourne : `{ query_params: { rooms__gte: 3, rooms__lte: 3, price__lte: 300000 }, search: "Angré" }`
3. Le backend applique : `rooms >= 3 AND rooms <= 3 AND price <= 300000 AND (title ILIKE '%Angré%' OR description ILIKE '%Angré%' OR city ILIKE '%Angré%' OR neighborhood ILIKE '%Angré%' OR address ILIKE '%Angré%')`
4. Résultat : trouve les annonces même si "Angré" n'est que dans l'adresse ou le titre

### Corrections appliquées

**`apps/api/views/listings.py`** :
- Ajout de `address` aux `search_fields` de DRF SearchFilter
- Avant : `['title', 'description', 'city', 'neighborhood']`
- Après : `['title', 'description', 'city', 'neighborhood', 'address']`

**`apps/core/services/ai/_prompts.py`** — Refonte complète du `SEARCH_INTENT_PROMPT` :
- Règle n°1 : TOUJOURS utiliser `search` pour la localisation (jamais city/neighborhood en filtre structuré)
- Exemples concrets de la géographie ivoirienne (communes → quartiers → sous-quartiers)
- Commodités et caractéristiques aussi dans `search`
- Seuls les filtres numériques (price, rooms, bedrooms, surface) et le type restent en filtres structurés

**`apps/core/services/ai/__init__.py`** — Post-processing `_broaden_location_filters()` :
- Filet de sécurité : si l'IA retourne quand même `city` ou `neighborhood` en filtre structuré, ils sont automatiquement extraits et fusionnés dans `search`
- Garantit que la localisation passe TOUJOURS par la recherche textuelle multi-champ

---

## 5b. Analyse TikTok — REJETÉ (8 avril 2026)

### Contexte
Recherche approfondie (deep research Gemini) sur l'intégration TikTok pour le partage d'annonces. Rapport complet dans `search_tiktokshare.md`.

### Décision : NE PAS implémenter maintenant

Raisons :
1. **MonaJent est une web app (Vue.js SPA)**, pas une app native. Le Share Kit TikTok nécessite un SDK natif iOS/Android.
2. **TikTok ne supporte pas les liens cliquables dans les légendes** — le modèle MonaJent repose entièrement sur le lien partageable avec aperçu riche. Sans lien cliquable, la conversion est quasi nulle.
3. **Le marché ivoirien fonctionne sur WhatsApp**, pas TikTok. Les agents partagent dans des groupes WhatsApp de 500+ membres.
4. **Processus d'audit TikTok lourd** : démonstration vidéo, module de divulgation commerciale, limite à 5 utilisateurs/24h avant audit, interdiction des filigranes (MonaJent utilise un watermark DRM).
5. **Barrière de création de contenu** : les agents ont du mal avec les photos, créer du contenu TikTok 9:16 est irréaliste.

### Quand reconsidérer
- Quand MonaJent a une **app mobile native** (PWA ou React Native)
- Quand il y a **+1000 agents actifs**
- Quand TikTok ouvre les **liens cliquables** pour le contenu organique

### Roadmap
TikTok placé dans **Horizon 2027**. Les ressources restent concentrées sur WhatsApp + Facebook.

---

## 8. Session 3 — Responsivité mobile, Mona IA vocale, Onboarding, PWA (8 avril 2026)

### 8a. Responsivité mobile des vues client (TERMINÉ)

**Problème** : Sur mobile, le bouton profil utilisateur ne fonctionnait pas, les pages client étaient inaccessibles, et les vidéos suggestions s'affichaient au-dessus du détail d'annonce (mauvais UX).

**Corrections** :

| Fichier | Modification |
|---------|-------------|
| `HomePage.vue` | `handleBottomNavProfile()` : sur mobile (≤768px), redirige directement vers `/home/dashboard` au lieu d'ouvrir un dropdown caché. Ajout de `activeBottomTab` computed pour l'état actif dynamique de la bottom nav. Avatar vert restauré dans l'onglet "Vous". |
| `ClientDashboard.vue` | Ajout liens rapides vers toutes les pages client (profil, support), bouton de déconnexion, avatar cliquable vers profil, grille responsive 2 colonnes sur mobile |
| `PublicListingView.vue` | Suppression de `order: -1` sur `.yw-right` en mobile → les suggestions vidéo s'affichent EN DESSOUS du détail (comme YouTube). Padding ajusté pour écrans ≤640px |

### 8b. Assistants vocaux Mona — MonaSearch + MonaAssistant (TERMINÉ)

Deux composants créés pour l'interaction vocale avec l'IA :

| Composant | Rôle | Utilisé dans |
|-----------|------|-------------|
| `MonaSearch.vue` | Recherche vocale IA pour les clients. FAB vert en bas à droite → panel avec phases welcome/recording/review/analyzing/done | `HomePage.vue` (vue publique) |
| `MonaAssistant.vue` | Saisie vocale pour créer des annonces agent. Même pattern de phases, mais l'analyse extrait les champs du formulaire | `AgentLayout.vue` (dashboard agent) |

**Fonctionnement** :
1. Phase `welcome` : message de bienvenue + bouton micro
2. Phase `recording` : écoute via `SpeechRecognition` API, affichage temps réel du transcript
3. Phase `review` : l'utilisateur relit/édite le texte, puis clique "Rechercher" ou "Analyser"
4. Phase `analyzing` : appel API IA → animation blocs + loupe/éclair
5. Phase `done` : résultats affichés (nombre d'annonces trouvées ou champs extraits)

**Fix speech-to-text Android Chrome** :
Sur Android Chrome (testé sur Techno Spark 40 Pro+), `SpeechRecognition` avec `continuous: true` causait des répétitions infinies et des arrêts automatiques.

Solution implémentée dans les deux composants :
- `r.continuous = !isMobile()` — désactivé sur mobile
- `baseTranscript` — accumule le texte finalisé entre les redémarrages de session
- `onresult` — reconstruit le transcript depuis `i=0` (pas `event.resultIndex`) pour éviter les doublons
- `onend` — redémarre automatiquement la reconnaissance sur mobile (simule continuous)
- `silenceTimer` (3.5s) — arrête l'écoute après un silence prolongé sur mobile
- Cleanup dans `stopRecording()`, `reset()`, `onBeforeUnmount()`

**Animation d'analyse** (phase `analyzing`) :
Le spinner circulaire simple a été remplacé par une grille de 9 blocs animés (shuffle, rotation, opacité décalée) avec une icône centrale :
- MonaSearch : loupe verte qui se déplace sur la grille
- MonaAssistant : éclair vert

**Icône FAB** :
Le FAB de MonaSearch utilise une bulle de chat blanche avec des sparkles verts (remplace l'ancien design confus avec cercle vert + loupe + M).

### 8c. Bulle d'invitation Mona + Son de notification (TERMINÉ)

**Comportement** :
- À chaque visite (après que l'onboarding soit terminé), une bulle blanche apparaît au-dessus du FAB après 1.5s
- Le son `discord-sounds.mp3` joue à chaque apparition (volume 50%)
- La bulle disparaît automatiquement après 5s
- Un `setInterval` de 30 secondes relance la bulle + son tant que l'utilisateur n'a pas ouvert l'assistant
- Dès que l'utilisateur ouvre le panel Mona, la boucle est définitivement arrêtée (`clearInviteLoop()`)
- Garde de sécurité : si la route n'est pas `/home*`, la boucle est stoppée (empêche le son de jouer sur le dashboard agent en PWA)
- Cliquer sur la bulle ouvre directement le panel Mona

**Salutations adaptées à l'heure** (`getGreeting()`) :
| Heure | Salutation |
|-------|-----------|
| 5h - 11h59 | "Bonjour" |
| 12h - 17h59 | "Bon après-midi" |
| 18h - 4h59 | "Bonsoir" |

Appliquée dans : bulle d'invitation (texte), synthèse vocale à l'ouverture du panel (MonaSearch + MonaAssistant), texte de bienvenue affiché (MonaAssistant).

### 8d. Onboarding Tour guidé (TERMINÉ)

**Composant** : `OnboardingTour.vue` — Tour guidé en 4 étapes avec spotlight et tooltips.

**Flux** :
1. L'utilisateur ferme le `WelcomeOverlay` (existant) → `@closed` est émis
2. `HomePage.vue` écoute l'événement et affiche `OnboardingTour` (si pas déjà complété)
3. Si le welcome a déjà été vu (sessionStorage/localStorage) mais l'onboarding pas terminé → se lance automatiquement après 800ms
4. Completion stockée dans `localStorage('monajent_onboarding_done')`

**Les 4 étapes** :

| # | Titre | Cible (mobile) | Cible (desktop) | Description |
|---|-------|----------------|-----------------|-------------|
| 1 | Les annonces en vidéo | _(centré, pas de spotlight)_ | _(centré)_ | Parcourez les biens en vidéo |
| 2 | Votre navigation | `[data-tour="nav"]` (bottom nav) | `[data-tour="sidebar"]` (sidebar) | Accueil, packs, favoris, espace perso |
| 3 | Les Packs de clés | `[data-tour="packs"]` (tab packs) | `[data-tour="sidebar-packs"]` (sidebar item) | Clés pour visites gratuites |
| 4 | Mona — Assistante IA | `[data-tour="mona"]` (FAB) | `[data-tour="mona"]` (FAB) | Recherche vocale IA |

**Sélecteurs adaptatifs** : chaque étape a un tableau de sélecteurs (`selectors`). `findVisibleEl()` teste chaque sélecteur et ne retient que le premier élément **réellement visible** (`width > 0 && height > 0`). Sur desktop, la bottom nav est cachée (display:none) → fallback sur la sidebar. Sur mobile, la sidebar est cachée → fallback sur la bottom nav.

**Positionnement intelligent du tooltip** :
- Cible haute et à gauche (sidebar desktop) → tooltip à droite
- Cible en bas (bottom nav, FAB) → tooltip au-dessus
- Pas de cible → tooltip centré dans la page

**Blocage des clics extérieurs** : l'utilisateur DOIT cliquer "Suivant" ou "Passer" — cliquer en dehors du tooltip ne fait rien.

**Spotlight** : `box-shadow: 0 0 0 9999px rgba(0,0,0,0.65)` sur un div positionné sur l'élément ciblé, avec `transition: all 0.4s` pour un mouvement fluide entre les étapes.

### 8e. PWA — Progressive Web App (TERMINÉ)

**Architecture** (implémentée manuellement, sans `vite-plugin-pwa` — réseau indisponible lors de l'installation) :

| Fichier | Rôle |
|---------|------|
| `public/manifest.webmanifest` | Manifeste PWA : `display: standalone`, `theme_color: #1DA53F`, `start_url: /home`, raccourcis Accueil + Favoris |
| `public/sw.js` | Service Worker : cache-first pour assets statiques, network-first pour pages HTML, ignore `/api/*` |
| `public/pwa-icon-{72,96,128,144,152,192,384,512}.png` | Icônes PWA toutes tailles (générées via Pillow depuis `logo_monajent_sf.png` 500x500) |
| `public/pwa-icon-maskable-512x512.png` | Icône maskable Android (logo centré à 70% sur fond blanc) |
| `public/apple-touch-icon-180x180.png` | Icône spécifique iOS |
| `src/components/PwaInstallPrompt.vue` | Banner d'installation avec bouton |

**Meta tags ajoutés dans `index.html`** :
```html
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#1DA53F">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="MonaJent">
<meta name="mobile-web-app-capable" content="yes">
```

**Enregistrement du Service Worker** (dans `index.html`) :
```html
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function () {})
    })
  }
</script>
```

**Service Worker — Stratégies de cache** :
- `GET /api/*` → Ignoré (toujours réseau)
- Assets (`.js`, `.css`, `.png`, `.webp`, `.woff2`, etc.) → **Cache-first** : sert depuis le cache, télécharge en background
- Pages HTML → **Network-first** : essaie le réseau, fallback sur le cache si hors-ligne
- Nettoyage : supprime les anciens caches lors de l'activation d'une nouvelle version

**PwaInstallPrompt.vue — Bouton d'installation** :
- **Android/Chrome/Edge** : intercepte `beforeinstallprompt`, affiche un banner avec bouton vert "Installer l'application" → déclenche le prompt natif
- **iOS Safari** : détecte l'appareil, affiche les instructions "Appuyez sur Partager → Sur l'écran d'accueil"
- Ne s'affiche PAS si l'app est déjà installée (`display-mode: standalone`)
- Mémorise le refus pendant 7 jours (`localStorage`)
- Responsive : au-dessus de la bottom nav sur mobile, en bas à droite sur desktop

**Pré-requis prod** : Le SW nécessite HTTPS. Sur `monajent.com` c'est déjà le cas.

### 8f. Fichiers créés/modifiés — Session 3

**Composants frontend créés** :

| Fichier | Lignes | Rôle |
|---------|--------|------|
| `src/components/MonaSearch.vue` | ~1141 | Recherche vocale IA client (FAB + panel + invite bubble + son) |
| `src/components/MonaAssistant.vue` | ~978 | Saisie vocale IA agent (FAB + panel) |
| `src/components/OnboardingTour.vue` | ~345 | Tour guidé 4 étapes avec spotlight adaptatif |
| `src/components/PwaInstallPrompt.vue` | ~160 | Banner d'installation PWA (Android + iOS) |

**Fichiers frontend modifiés** :

| Fichier | Modifications principales |
|---------|--------------------------|
| `index.html` | Meta PWA, manifest link, apple-touch-icon, enregistrement SW |
| `src/views/HomePage.vue` | Import MonaSearch, OnboardingTour, PwaInstallPrompt. `data-tour` sur bottom nav + sidebar. `onWelcomeClosed()`, `showOnboarding` logic. `activeBottomTab`, `handleBottomNavProfile()` mobile. |
| `src/views/client/ClientDashboard.vue` | Liens rapides, bouton déconnexion, avatar profil, grille responsive |
| `src/views/public/PublicListingView.vue` | Layout mobile corrigé (suggestions en dessous), padding ajusté |
| `src/components/WelcomeOverlay.vue` | `defineEmits(['closed'])`, émet sur handleUnderstood/handleNeverShow |

**Assets PWA créés** (`frontend/public/`) :

`pwa-icon-72x72.png`, `pwa-icon-96x96.png`, `pwa-icon-128x128.png`, `pwa-icon-144x144.png`, `pwa-icon-152x152.png`, `pwa-icon-192x192.png`, `pwa-icon-384x384.png`, `pwa-icon-512x512.png`, `pwa-icon-maskable-512x512.png`, `apple-touch-icon-180x180.png`, `manifest.webmanifest`, `sw.js`

**Audio** : `src/assets/media/discord-sounds.mp3` — son de notification pour la bulle Mona

### 8g. Bug fix — Son Mona sur dashboard agent en PWA

**Problème** : Sur Techno Spark 40 en PWA, le son discord jouait toutes les 30s sur le dashboard agent (mais sans bulle visible).

**Cause** : Le PWA a `start_url: /home`. Quand un agent ouvre l'app, HomePage.vue se monte brièvement (timer démarré), puis la guard redirige vers `/agent`. Par une race condition, l'interval pouvait survivre au démontage.

**Fix** : Ajout d'une garde dans `showInviteBubble()` :
```js
if (!route.path.startsWith('/home')) { clearInviteLoop(); return }
```
Si le composant est actif mais la route n'est pas `/home*`, la boucle est définitivement stoppée.

---

## 6. Ce qui reste à faire (suggestions)

### Technique — URGENT (déploiement)
- [ ] **Déployer en prod** : rebuild frontend + backend (tout ce qui a changé en sessions 1-3)
- [ ] **Tester les aperçus WhatsApp** avec un lien JAMAIS partagé auparavant (cache WhatsApp = 7 jours)
- [ ] **Tester la recherche Mona** : vérifier que "Angré", "Cocody", etc. trouvent bien les annonces existantes
- [ ] **Tester la PWA** : vérifier l'installation sur Android Chrome + iOS Safari en prod (nécessite HTTPS)
- [ ] **Tester le speech-to-text** : vérifier sur Android Chrome, Samsung Internet, iOS Safari
- [ ] `BACKEND_BASE_URL` n'est plus nécessaire pour les URLs OG (utilise `FRONTEND_URL` maintenant), mais le garder pour d'autres usages éventuels

### Technique — Court terme
- [ ] Allonger l'expiration des annonces de 7 à 30 jours (phase de lancement)
- [ ] Permettre la publication SANS KYC (KYC différé après 3 annonces) pour réduire la friction
- [ ] Ajouter le partage **Telegram** (bouton dans ShareDialog + PublicListingView)
- [ ] Améliorer le Service Worker : pré-cacher les annonces favorites pour consultation hors-ligne
- [ ] Ajouter des screenshots au manifest.webmanifest pour un install prompt plus riche sur Android

### Technique — Moyen terme
- [ ] Notifications push (FCM) pour agents et clients
- [ ] Packs variés (500 / 2 000 / 5 000 FCFA)
- [ ] Gamification agents (badges, classement, top agents)
- [x] ~~PWA (Progressive Web App) pour l'installation mobile~~ ✅ Session 3
- [x] ~~Responsivité mobile des vues client~~ ✅ Session 3
- [x] ~~Assistants vocaux Mona (MonaSearch + MonaAssistant)~~ ✅ Session 3
- [x] ~~Onboarding tour pour les nouveaux utilisateurs~~ ✅ Session 3
- [ ] Mode hors-ligne complet pour la consultation d'annonces favorites
- [ ] TikTok (Horizon 2027 — voir section 5b)

### Business — Immédiat
- [ ] Trouver 10 agents early-adopters (réseau personnel)
- [ ] Les aider à publier 5 annonces chacun via Mona
- [ ] Leur montrer comment partager les liens dans leurs groupes WhatsApp
- [ ] Mesurer : clics sur liens, packs achetés, vues vidéo
- [ ] Créer un groupe WhatsApp "Agents MonaJent" pour la communauté

---

## 7. Commandes utiles

```bash
# Backend — Lancer le serveur dev
cd monajent/backend && source venv/bin/activate && python manage.py runserver

# Backend — Vérifier les providers IA enregistrés
cd monajent/backend && python3 -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from apps.core.services.ai._registry import get_providers
for p in get_providers():
    print(f'{p.priority:3d} {p.name:<12s} [{\"ACTIF\" if p.is_available() else \"inactif\"}]')
"

# Backend — Tester le partage OG (simule WhatsApp)
curl -H "User-Agent: WhatsApp/2.0" "http://localhost:8000/api/share/<slug>/"

# Backend — Tester le proxy image
curl -o /dev/null -w "%{http_code} %{content_type} %{size_download}b" "http://localhost:8000/api/share/<slug>/image.jpg"

# Backend — Tests unitaires IA
cd monajent/backend && python manage.py test apps.core.tests.test_gemini_ai

# Frontend — Dev server
cd monajent/frontend && npm run dev

# Build prod (Docker)
export VITE_API_BASE_URL=https://api.monajent.com
docker buildx bake -f docker-compose.build.yml --builder cloud-ciacems-ciacems-builder --push
```



Smartphones (Téléphones)
iPhone SE : 375 x 667 px
iPhone XR : 414 x 896 px
iPhone 12 Pro : 390 x 844 px
iPhone 14 Pro Max : 430 x 932 px
Pixel 7 : 412 x 915 px
Samsung Galaxy S8+ : 360 x 740 px
Samsung Galaxy S20 Ultra : 412 x 915 px
Samsung Galaxy A51/71 : 412 x 914 px
Tablettes et Pliables
iPad Mini : 768 x 1024 px
iPad Air : 820 x 1180 px
iPad Pro : 1024 x 1366 px
Surface Pro 7 : 912 x 1368 px
Surface Duo : 540 x 720 px (un seul écran)
Galaxy Z Fold 5 : 344 x 882 px (écran plié) / 673 x 796 px (écran déplié)
Asus Zenbook Fold : 853 x 1280 px (plié) / 1280 x 1707 px (déplié)
Écrans Connectés (Smart Displays)
Nest Hub : 1024 x 600 px
Nest Hub Max : 1280 x 800 px
Note technique : Ces valeurs correspondent aux "points" (Viewport). Pour obtenir la résolution physique réelle, il faut multiplier ces chiffres par le Device Pixel Ratio (DPR) de l'appareil (souvent x2 ou x3 pour les écrans Retina/OLED).