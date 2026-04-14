"""Prompts IA pour l'immobilier en Côte d'Ivoire — séparés de la logique provider."""

EXTRACTABLE_FIELDS: dict[str, str] = {
    'title': 'Titre',
    'description': 'Description',
    'listing_type': 'Type (Location/Vente)',
    'city': 'Ville',
    'neighborhood': 'Quartier',
    'address': 'Adresse',
    'price': 'Prix',
    'rooms': 'Nombre de pièces',
    'bedrooms': 'Chambres',
    'bathrooms': 'Salles de bain',
    'surface_m2': 'Surface (m²)',
    'furnishing': 'Ameublement',
    'amenities': 'Commodités',
    'deposit_months': 'Caution (mois)',
    'advance_months': 'Avance (mois)',
    'agency_fee_months': 'Frais d\'agence (mois)',
    'other_conditions': 'Autres conditions',
}

LISTING_EXTRACTION_PROMPT = """Tu es un expert immobilier en Côte d'Ivoire. Analyse le texte suivant et extrais TOUS les champs possibles pour un formulaire d'annonce immobilière.

TEXTE DE L'AGENT :
---
{text}
---

RÈGLES D'INTERPRÉTATION :
- "2+2+1" ou "5 mois" = 2 mois de caution, 2 mois d'avance, 1 mois d'agence. "3+3+1" = 3 caution, 3 avance, 1 agence. Adapte selon la formule donnée.
- "3 pièces" = 3 pièces totales (salon + chambres). Si l'agent dit "3 pièces", rooms=3 et bedrooms=2 (1 salon déduit). Si "2 chambres salon", rooms=3, bedrooms=2. Adapte selon le contexte.
- "Studio" = rooms=1, bedrooms=0 ou 1 selon le contexte.
- Prix en francs CFA entier (nombre sans séparateurs). "250k" = 250000, "1.5M" = 1500000, "1 million" = 1000000.
- listing_type : "LOCATION" (loyer, bail) ou "VENTE" (achat, vendre) — déduis du contexte. Par défaut "LOCATION" si ambigu.
- furnishing : "" si non mentionné, "FURNISHED" si meublé, "UNFURNISHED" si non meublé/vide, "SEMI_FURNISHED" si semi-meublé/équipé cuisine.
- amenities : liste de chaînes courtes. Exemples courants CI : "parking", "gardien", "eau courante", "électricité", "clim", "balcon", "terrasse", "piscine", "groupe électrogène", "forage". Extrais tout ce qui est mentionné.
- title : génère un titre accrocheur et professionnel basé sur le type, le nombre de pièces, le quartier et la ville. Ex: "Appartement 3 pièces Cocody Riviera".
- description : reformule proprement le texte de l'agent en 2-3 phrases descriptives et professionnelles.
- surface_m2 : extrais si mentionné (ex. "80m²", "80 mètres carrés"). Sinon null.
- bathrooms : extrais si mentionné ("2 douches", "1 sdb"). Sinon null.
- other_conditions : tout ce qui ne rentre pas dans les champs ci-dessus (ex. "pas d'animaux", "célibataire uniquement").

LOCALISATION (TRÈS IMPORTANT) :
- city : la ville principale (Abidjan, Bouaké, Yamoussoukro, etc.).
- neighborhood : le quartier (Cocody, Plateau, Marcory, Yopougon, Angré, Riviera Faya, Djorogobité, etc.).
- address : construis une adresse exploitable à partir de TOUS les indices de localisation mentionnés. Combine quartier, sous-quartier, repères, numéros de lot, etc. Ex: si l'agent dit "Angré CHU derrière la pharmacie du CHU", mets "Angré, à proximité du CHU".
- latitude / longitude : estime les coordonnées GPS approximatives du lieu si tu reconnais le quartier/adresse en Côte d'Ivoire. Utilise tes connaissances géographiques. Exemples de coordonnées connues :
  * Cocody Angré : 5.3600, -3.9900
  * Cocody Riviera Faya : 5.3480, -3.9650
  * Plateau (centre Abidjan) : 5.3200, -4.0170
  * Marcory : 5.3050, -3.9850
  * Yopougon : 5.3450, -4.0700
  * Koumassi : 5.2950, -3.9550
  * Treichville : 5.3050, -4.0100
  * Djorogobité : 5.3750, -3.9750
  Si tu ne connais pas la position exacte du sous-quartier, utilise les coordonnées du quartier principal le plus proche. Si tu ne reconnais pas du tout le lieu, mets null.

CHAMPS NON EXTRACTIBLES (ne les mets JAMAIS) :
- agent_note (note privée de l'agent)
- status (géré automatiquement par le système)

IMPORTANT SUR LES CHAMPS MANQUANTS :
- Remplis UNIQUEMENT les champs dont tu trouves l'information dans le texte.
- Pour chaque champ NON mentionné dans le texte, mets null (nombres/objets) ou "" (chaînes) ou [] (listes).
- Ajoute un champ "missing_fields" : une liste de chaînes avec les NOMS FRANÇAIS des champs que l'agent n'a PAS mentionnés et qu'il devrait compléter manuellement. Sois utile et précis.
- NE mets PAS "Position sur la carte" dans missing_fields si tu as pu estimer latitude/longitude.

Réponds UNIQUEMENT avec un objet JSON (pas de markdown, pas de texte avant ou après) :
{{
  "title": string,
  "description": string,
  "listing_type": "LOCATION" | "VENTE",
  "city": string,
  "neighborhood": string,
  "address": string,
  "latitude": number | null,
  "longitude": number | null,
  "price": number | null,
  "rooms": number | null,
  "bedrooms": number | null,
  "bathrooms": number | null,
  "surface_m2": number | null,
  "furnishing": string,
  "amenities": string[],
  "deposit_months": number | null,
  "advance_months": number | null,
  "agency_fee_months": number | null,
  "other_conditions": string,
  "missing_fields": string[]
}}"""


SEARCH_INTENT_PROMPT = """Tu assistes un site immobilier en Côte d'Ivoire. À partir de la phrase utilisateur, produis des filtres pour l'API de recherche.

PHRASE :
---
{text}
---

═══ RÈGLE N°1 — LOCALISATION → TOUJOURS dans "search" ═══

Mets TOUS les termes de localisation (ville, commune, quartier, sous-quartier, repères) dans le champ "search".
N'utilise JAMAIS city, city__icontains, neighborhood, neighborhood__icontains — ces filtres sont trop stricts et ratent des résultats.
Le champ "search" cherche dans le titre, la description, la ville, le quartier ET l'adresse de chaque annonce (recherche large).

TRÈS IMPORTANT — CONSERVE LA PHRASE DE LOCALISATION COMPLÈTE :
Les agents en Côte d'Ivoire mettent souvent la localisation complète dans le TITRE de l'annonce
(ex: "Studio meublé Yopougon Maroc", "Villa duplex Cocody Angré"). Tu DOIS garder la phrase
de localisation EXACTEMENT comme l'utilisateur la dit pour que le moteur de recherche la retrouve dans les titres.
Ne supprime JAMAIS une partie de la localisation, même si elle semble redondante.

ATTENTION — Noms de quartiers ivoiriens qui ressemblent à des noms de pays/villes étrangers :
Ces noms sont des QUARTIERS en Côte d'Ivoire, PAS des pays. Ne les interprète JAMAIS autrement :
- "Maroc" → quartier de Yopougon (PAS le pays Maroc)
- "Canada" → quartier de Yopougon
- "Washington" → quartier de Cocody
- "Dallas" → quartier d'Abobo
- "New York" → quartier de Treichville
- "Sicogi" → quartier de Yopougon
Quand l'utilisateur dit "Yopougon Maroc", c'est 100% un quartier ivoirien.

CORRECTION SAISIE VOCALE — TRÈS IMPORTANT :
Les utilisateurs dictent souvent leur recherche. Le moteur de reconnaissance vocale (speech-to-text)
déforme les noms de quartiers ivoiriens en mots français/anglais qui « sonnent » pareil.
Tu DOIS reconnaître ces déformations et les CORRIGER vers le vrai nom du quartier dans "search".

Déformations fréquentes (saisie vocale → nom réel) :
- "Angry", "angry", "André", "en gré", "angré" → Angré
- "Coco dit", "cocodie", "Kokodi", "coco di" → Cocody
- "You pou gon", "yopoungon", "yopu gon" → Yopougon
- "Marc Ori", "ma corie", "Marcori" → Marcory
- "Djoro go biter", "joro go bité", "jorogobité" → Djorogobité
- "A jamais", "adja mais", "Adjamais" → Adjamé
- "Coumassie", "Coumassi", "cou massi" → Koumassi
- "de plateaux", "deux plats tôt", "de plato" → Deux Plateaux
- "Riviera faillat", "riviera faillah", "riviera faya" → Riviera Faya
- "Treich ville", "très ville" → Treichville
- "Niangone", "nianon" → Niangon
- "Port bouais", "port bouet" → Port-Bouët
- "grand bas ça m", "grand bas ça me" → Grand-Bassam
- "bou à ké", "bouaquer" → Bouaké
- "Yamoussoukro" est généralement bien reconnu

Si tu détectes un mot qui ressemble phonétiquement à un quartier/commune ivoirien,
REMPLACE-LE par l'orthographe correcte dans "search". L'utilisateur ne tape pas, il parle.

Exemples :
- "appartement à Cocody" → search: "Cocody"
- "maison Angré 9ème tranche" → search: "Angré 9ème tranche"
- "studio Riviera Faya" → search: "Riviera Faya"
- "bien à Yopougon Maroc" → search: "Yopougon Maroc"
- "location Yopougon Maroc" → search: "Yopougon Maroc"
- "studio meublé Yopougon" → search: "Yopougon"
- "3 pièces Abidjan Plateau" → search: "Plateau"  (pas "Abidjan" car trop large si un quartier est précisé)
- "villa Cocody Angré" → search: "Cocody Angré"
- "appartement Abobo Dallas" → search: "Abobo Dallas"
- "maison angry" → search: "Angré"  (correction vocale : angry → Angré)
- "studio coco dit" → search: "Cocody"  (correction vocale : coco dit → Cocody)
- "location à jorogobité" → search: "Djorogobité"  (correction vocale)
- "3 pièces a jamais" → search: "Adjamé"  (correction vocale : a jamais → Adjamé)

Si l'utilisateur mentionne une commodité ou caractéristique (piscine, gardien, parking, vue, etc.), ajoute-la aussi dans search.
Exemple : "appartement avec piscine Cocody" → search: "Cocody piscine"

═══ RÈGLE N°2 — FILTRES STRUCTURÉS (numériques et type) ═══

Utilise les filtres structurés UNIQUEMENT pour les critères numériques et le type :
- listing_type : "LOCATION" (loyer/bail) ou "VENTE" (achat). Omettre si non mentionné.
- price__gte, price__lte : prix en CFA. "250k" = 250000, "1.5M" = 1500000.
  · "budget 300k" → price__lte: 300000
  · "entre 200k et 400k" → price__gte: 200000, price__lte: 400000
  · "à partir de 150k" → price__gte: 150000
- rooms__gte, rooms__lte : nombre de pièces. "3 pièces" → rooms__gte: 3, rooms__lte: 3
- bedrooms__gte, bedrooms__lte : chambres. "au moins 2 chambres" → bedrooms__gte: 2
- surface_m2__gte, surface_m2__lte : surface en m².
- furnishing : "FURNISHED", "UNFURNISHED" ou "SEMI_FURNISHED". Omettre si non mentionné.

═══ GÉOGRAPHIE CÔTE D'IVOIRE ═══

Comprends la hiérarchie pour mieux interpréter la requête :
- Abidjan → Communes : Cocody, Plateau, Marcory, Yopougon, Koumassi, Treichville, Abobo, Adjamé, Port-Bouët
- Cocody → Quartiers : Angré, Riviera, Riviera Faya, Deux Plateaux, Djorogobité, Riviera 2, Riviera 3, Riviera Palmeraie
- Angré → Sous-quartiers : 7ème/8ème/9ème Tranche, Nouveau CHU, Star, Château, Djibi
- Yopougon → Quartiers : Maroc (quartier, PAS le pays !), Niangon, Selmer, Millionnaire, Toits Rouges, Sideci, Canada, Sicogi, Banco
- Marcory → Quartiers : Zone 4, Anoumabo, Résidentiel

Si l'utilisateur dit un sous-quartier (ex: "Angré"), mets "Angré" dans search (pas "Cocody" seul).
Si l'utilisateur dit une commune (ex: "Cocody"), mets "Cocody" dans search (trouvera tous les quartiers de Cocody).
Si l'utilisateur dit seulement "Abidjan", mets "Abidjan" dans search.

═══ ORDONNANCEMENT ═══

- ordering : "price", "-price", "created_at", "-created_at", "views_count", "-views_count"
- "moins cher" → ordering: "price"
- "plus récent" → ordering: "-created_at"
- Si non mentionné, ne mets pas d'ordering.

═══ RÉPONSE ═══

Réponds UNIQUEMENT avec un objet JSON :
{{
  "query_params": {{ ...filtres structurés uniquement (listing_type, price, rooms, bedrooms, surface_m2, furnishing)... }},
  "search": "termes de localisation et mots-clés" ou null,
  "ordering": "champ" ou null
}}

Les valeurs numériques doivent être des nombres JSON (pas des chaînes).
"""
