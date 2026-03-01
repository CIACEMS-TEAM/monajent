# Systeme Anti-Fraude Video — MonaJent

## Problematique

Le modele economique de MonaJent repose sur le **pay-per-view** : les clients
paient (en cles virtuelles) pour visionner les videos des biens immobiliers.
Un agent malhonnete pourrait tenter de **reutiliser la meme video** sur
plusieurs annonces fictives pour multiplier ses revenus.

Il faut donc garantir : **1 video unique = 1 bien reel = 1 annonce**.

---

## Architecture — Double couche de detection

```
┌──────────────────────────────────────────────────────────────┐
│                    AGENT SELECTIONNE UNE VIDEO               │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  COUCHE 0 — Pre-check cote client (navigateur)              │
│                                                              │
│  • Calcul SHA-256 via Web Crypto API (SubtleCrypto)          │
│  • Envoi du hash seul → POST /api/agent/videos/precheck/     │
│  • Si doublon exact detecte → REJET IMMEDIAT                 │
│    (zero bande passante gaspillee)                           │
│  • Si OK → upload du fichier complet                         │
└──────────────────────┬───────────────────────────────────────┘
                       │ upload
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  COUCHE 1 — SHA-256 cote serveur (doublons exacts)           │
│                                                              │
│  • Recalcul SHA-256 du fichier recu (hashlib, blocs 8 Ko)    │
│  • Comparaison avec TOUTES les videos de l'agent             │
│    (tous statuts d'annonces confondus)                       │
│  • Si hash identique existe → DuplicateVideoError (exact)    │
└──────────────────────┬───────────────────────────────────────┘
                       │ hash unique
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  COUCHE 2 — Hash perceptuel (copies modifiees)               │
│                                                              │
│  • Ecriture temp du fichier                                  │
│  • Calcul via VideoHash (Python) :                           │
│    - Extraction des frames cles (FFmpeg)                     │
│    - Generation d'un hash 64-bit base sur le contenu visuel  │
│  • Comparaison par distance de Hamming avec les hash         │
│    existants de l'agent                                      │
│  • Si distance ≤ 10 bits → DuplicateVideoError (perceptual)  │
│  • Si OK → sauvegarde des deux hash + fichier video          │
└──────────────────────────────────────────────────────────────┘
```

---

## Tableau comparatif des couches

| Couche | Methode | Detecte | Vitesse | Contourne par |
|--------|---------|---------|---------|---------------|
| 0 | SHA-256 client (SubtleCrypto) | Doublons exacts | Instantane (~ms) | Edition du fichier |
| 1 | SHA-256 serveur (hashlib) | Doublons exacts | Tres rapide (~ms) | Edition du fichier |
| 2 | VideoHash perceptuel | Copies recompressees, recadrees, filtrees | Plus lent (~sec) | Re-tournage complet |

---

## Regles metier

| Regle | Description |
|-------|-------------|
| **Inter-agents** | Deux agents differents **PEUVENT** avoir la meme video (cas de mandat partage sur un meme bien) |
| **Intra-agent** | Un agent **NE PEUT PAS** utiliser la meme video sur deux annonces differentes |
| **Tous statuts** | La verification couvre les annonces ACTIF, INACTIF, EXPIRED et SUSPENDED |
| **Meme annonce** | Le remplacement d'une video sur la meme annonce est autorise (`exclude_listing_id`) |

---

## Implementation technique

### Modele `Video` (Django)

```python
# apps/listings/models.py

class Video(models.Model):
    file = models.FileField(upload_to='listings/videos/')
    
    # Couche 1 : empreinte exacte
    file_hash = models.CharField(
        max_length=64, blank=True, db_index=True,
        help_text='SHA-256 du fichier video'
    )
    
    # Couche 2 : empreinte perceptuelle
    perceptual_hash = models.CharField(
        max_length=16, blank=True, db_index=True,
        help_text='Hash perceptuel 64-bit (hex) via VideoHash'
    )
```

### Service `video_dedup.py`

```
apps/core/services/video_dedup.py
```

**Fonctions principales :**

| Fonction | Role |
|----------|------|
| `compute_file_hash(file)` | Calcule le SHA-256 d'un fichier uploade |
| `check_exact_duplicate(agent, hash)` | Cherche un doublon exact dans les videos de l'agent |
| `check_hash_exists(agent, hash)` | Version rapide pour le pre-check API |
| `compute_perceptual_hash(file)` | Calcule le hash perceptuel via VideoHash |
| `check_perceptual_duplicate(agent, phash)` | Compare par distance de Hamming (seuil = 10) |
| `validate_and_hash_video(agent, file)` | Pipeline complet : SHA-256 puis perceptuel |

**Exception :** `DuplicateVideoError(existing_video, method='exact'|'perceptual')`

### Endpoint pre-check

```
POST /api/agent/videos/precheck/
Content-Type: application/json

{ "file_hash": "a1b2c3...64 hex chars" }
```

**Reponses :**

```json
// Pas de doublon
{ "duplicate": false }

// Doublon detecte
{
  "duplicate": true,
  "listing_id": 42,
  "listing_title": "Appartement 3p Cocody"
}
```

### Frontend (SubtleCrypto)

```typescript
// Calcul SHA-256 natif dans le navigateur
async function computeFileSha256(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}
```

Le hash est calcule **localement** avant tout envoi reseau. Si le pre-check
detecte un doublon, le fichier n'est jamais uploade.

---

## Distance de Hamming — Seuil perceptuel

Le hash perceptuel est une chaine hexadecimale de 16 caracteres (64 bits).
Deux videos visuellement identiques auront des hash tres proches.

```
Video A : 0a1b2c3d4e5f6789
Video B : 0a1b2c3d4e5f6788  → distance = 1 bit  → BLOQUE (≤ 10)
Video C : ff00ff00ff00ff00  → distance = 32 bits → AUTORISE (> 10)
```

**Seuil configurable :** `PERCEPTUAL_HAMMING_THRESHOLD = 10` dans `video_dedup.py`

- **0-5 bits** : videos quasi-identiques (meme source, compression differente)
- **6-10 bits** : copies avec modifications mineures (recadrage, filtre)
- **> 10 bits** : videos differentes

---

## Dependances systeme

### Python (requirements.txt)

```
videohash==3.0.1
ImageHash==4.3.2
numpy==2.4.2
scipy==1.17.1
```

### Systeme

```bash
# Requis par VideoHash pour l'extraction des frames
apt-get install -y ffmpeg
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Dependance systeme pour VideoHash
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

---

## Flux complet — Diagramme de sequence

```
Agent (navigateur)              Backend Django
    │                                │
    │  [1] Selectionne video.mp4     │
    │  [2] Calcul SHA-256 local      │
    │                                │
    │  POST /videos/precheck/        │
    │  { file_hash: "abc123..." }    │
    │ ─────────────────────────────► │
    │                                │  [3] check_hash_exists()
    │  { duplicate: false }          │
    │ ◄───────────────────────────── │
    │                                │
    │  POST /listings/7/videos/      │
    │  [multipart: video.mp4]        │
    │ ─────────────────────────────► │
    │                                │  [4] compute_file_hash() → SHA-256
    │                                │  [5] check_exact_duplicate()
    │                                │  [6] compute_perceptual_hash() → VideoHash
    │                                │  [7] check_perceptual_duplicate()
    │                                │  [8] save(file_hash, perceptual_hash)
    │                                │
    │  201 Created                   │
    │ ◄───────────────────────────── │
```

---

## Messages d'erreur utilisateur

| Situation | Message affiche |
|-----------|----------------|
| Pre-check SHA-256 positif | "Cette video est deja utilisee sur l'annonce « {titre} » (ID #{id}). Chaque annonce doit avoir sa propre video." |
| Doublon exact serveur | "Video identique deja utilisee sur l'annonce « {titre} » (ID #{id}). Chaque annonce doit avoir sa propre video." |
| Doublon perceptuel | "Video visuellement similaire deja utilisee sur l'annonce « {titre} » (ID #{id}). Chaque annonce doit avoir sa propre video." |

---

## Limites connues

1. **Re-tournage complet** : Si l'agent re-filme le meme bien sous un angle
   different, le hash perceptuel sera different. Ceci est acceptable car
   cela represente un effort reel (et potentiellement un bien different).

2. **Performance** : Le calcul VideoHash prend quelques secondes par video
   (extraction de frames). Pour le MVP c'est synchrone ; en production,
   envisager un traitement asynchrone via Celery.

3. **Faux positifs** : Le seuil de 10 bits est conservateur. Si des faux
   positifs apparaissent, augmenter `PERCEPTUAL_HAMMING_THRESHOLD`.

4. **Videos tres courtes** : Les videos de moins de 2 secondes peuvent
   generer des hash perceptuels peu fiables. VideoHash necessite un minimum
   de contenu visuel pour etre pertinent.
