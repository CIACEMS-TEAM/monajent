"""
Package IA MonaJent — API publique.

Architecture :
  _registry.py       → Protocol + registre auto-discovery
  _prompts.py        → Prompts métier (immobilier CI)
  _parsing.py        → Parsing JSON commun
  providers/         → Un module par fournisseur, auto-enregistré
  exceptions.py      → Exceptions partagées

Pour ajouter un nouveau provider (ex. DeepSeek, Mistral, OpenRouter) :
  1. Créer providers/deepseek.py
  2. Implémenter _is_available() et _generate(prompt) -> str
  3. Appeler register_provider(name, priority, is_available, generate)
  Rien d'autre à modifier.
"""

from __future__ import annotations

import logging
from typing import Any

from ._parsing import parse_model_json
from ._prompts import EXTRACTABLE_FIELDS, LISTING_EXTRACTION_PROMPT, SEARCH_INTENT_PROMPT
from ._registry import get_providers
from .exceptions import (
    AIConfigurationError,
    AIParseError,
    AIProviderError,
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiParseError,
)

# L'import de providers/ déclenche l'auto-discovery
from . import providers as _providers  # noqa: F401

logger = logging.getLogger(__name__)

__all__ = [
    'extract_listing_from_text',
    'parse_search_intent',
    'parse_model_json',
    'AIConfigurationError',
    'AIParseError',
    'AIProviderError',
    'GeminiConfigurationError',
    'GeminiParseError',
    'GeminiAPIError',
]


# ─── Orchestrateur ───────────────────────────────────────────────────────────

def _is_rate_limit(exc: Exception) -> bool:
    s = str(exc).lower()
    return '429' in s or 'resource_exhausted' in s or 'rate_limit' in s


def _generate_text(prompt: str) -> str:
    """Essaie chaque provider enregistré par ordre de priorité."""
    available = [p for p in get_providers() if p.is_available()]

    if not available:
        raise AIConfigurationError(
            'Aucun fournisseur IA configuré (GROQ_API_KEY ou GEMINI_API_KEY requis).'
        )

    last_exc: Exception | None = None
    for provider in available:
        try:
            result = provider.generate(prompt)
            logger.debug('ai: %s responded ok', provider.name)
            return result
        except Exception as e:
            last_exc = e
            logger.warning('ai %s failed: %s', provider.name, str(e)[:200])
            continue

    logger.error('ai: all providers failed')
    if last_exc and _is_rate_limit(last_exc):
        raise AIProviderError(
            'Mona est très sollicitée en ce moment. '
            'Veuillez réessayer dans quelques secondes.'
        ) from last_exc
    raise AIProviderError(
        'Mona rencontre un problème temporaire. '
        'Veuillez réessayer dans un instant.'
    ) from last_exc


# ─── Fonctions publiques (interface stable) ──────────────────────────────────

def extract_listing_from_text(text: str) -> dict[str, Any]:
    prompt = LISTING_EXTRACTION_PROMPT.format(text=text.strip())
    raw = _generate_text(prompt)
    data = parse_model_json(raw)
    if 'missing_fields' not in data or not isinstance(data.get('missing_fields'), list):
        data['missing_fields'] = _compute_missing_fields(data)
    return data


def _compute_missing_fields(data: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key, label in EXTRACTABLE_FIELDS.items():
        val = data.get(key)
        if val is None or val == '' or val == []:
            missing.append(label)
    return missing


def parse_search_intent(text: str) -> dict[str, Any]:
    prompt = SEARCH_INTENT_PROMPT.format(text=text.strip())
    raw = _generate_text(prompt)
    data = parse_model_json(raw)
    qp = data.get('query_params')
    if qp is not None and not isinstance(qp, dict):
        raise AIParseError('query_params doit être un objet.')
    if qp is None:
        data['query_params'] = {}
    _broaden_location_filters(data)
    _ensure_search_from_text(data, text)
    return data


_LOCATION_KEYS = frozenset({
    'city', 'city__icontains',
    'neighborhood', 'neighborhood__icontains',
})


def _broaden_location_filters(data: dict[str, Any]) -> None:
    """Move structured location filters → 'search' for broader multi-field matching.

    Even if the prompt says not to, the LLM sometimes still returns city/neighborhood
    as structured filters.  Those do exact or single-field icontains matching and miss
    results.  The DRF SearchFilter 'search' param does icontains across title,
    description, city, neighborhood AND address — much more forgiving.
    """
    qp = data.get('query_params', {})
    location_terms: list[str] = []

    for key in list(qp):
        if key in _LOCATION_KEYS:
            val = qp.pop(key)
            if val and isinstance(val, str) and val.strip():
                location_terms.append(val.strip())

    existing = (data.get('search') or '').strip()
    merged = ' '.join(filter(None, [existing] + location_terms))
    if merged:
        data['search'] = merged


_KNOWN_LOCATIONS: set[str] = {
    # Communes d'Abidjan
    'cocody', 'plateau', 'marcory', 'yopougon', 'koumassi',
    'treichville', 'abobo', 'adjamé', 'adjame', 'port-bouët', 'port bouet',
    'attécoubé', 'attecoube', 'songon', 'bingerville', 'anyama',
    # Quartiers fréquents
    'angré', 'angre', 'riviera', 'riviera faya', 'deux plateaux',
    'djorogobité', 'djorogobite', 'palmeraie', 'vallon',
    'zone 4', 'anoumabo', 'résidentiel',
    'maroc', 'niangon', 'selmer', 'millionnaire', 'toits rouges',
    'sideci', 'sicogi', 'banco', 'canada', 'washington', 'dallas',
    # Villes hors Abidjan
    'bouaké', 'bouake', 'yamoussoukro', 'san pedro', 'grand-bassam',
    'grand bassam', 'bassam', 'assinie', 'dabou', 'aboisso',
}

_VOICE_CORRECTIONS: dict[str, str] = {
    # Angré
    'angry': 'angré', 'andré': 'angré', 'en gré': 'angré',
    # Cocody
    'coco dit': 'cocody', 'cocodie': 'cocody', 'kokodi': 'cocody',
    'coco di': 'cocody',
    # Yopougon
    'you pou gon': 'yopougon', 'yopoungon': 'yopougon',
    'yopu gon': 'yopougon',
    # Marcory
    'marc ori': 'marcory', 'ma corie': 'marcory', 'marcori': 'marcory',
    # Djorogobité
    'jorogobité': 'djorogobité', 'jorogobite': 'djorogobité',
    'djoro go biter': 'djorogobité', 'joro go bité': 'djorogobité',
    # Adjamé
    'a jamais': 'adjamé', 'adja mais': 'adjamé', 'adjamais': 'adjamé',
    # Koumassi
    'coumassie': 'koumassi', 'cou massi': 'koumassi',
    # Deux Plateaux
    'de plateaux': 'deux plateaux', 'deux plats tôt': 'deux plateaux',
    'de plato': 'deux plateaux',
    # Riviera Faya
    'riviera faillat': 'riviera faya', 'riviera faillah': 'riviera faya',
    # Treichville
    'treich ville': 'treichville', 'très ville': 'treichville',
    # Niangon
    'niangone': 'niangon', 'nianon': 'niangon',
    # Port-Bouët
    'port bouais': 'port-bouët',
    # Grand-Bassam
    'grand bas ça m': 'grand-bassam',
    # Bouaké
    'bou à ké': 'bouaké', 'bouaquer': 'bouaké',
}


def _apply_voice_corrections(text: str) -> str:
    """Corrige les déformations de saisie vocale dans le texte utilisateur."""
    text_lower = text.lower()
    for wrong, correct in sorted(_VOICE_CORRECTIONS.items(), key=lambda x: len(x[0]), reverse=True):
        if wrong in text_lower:
            text_lower = text_lower.replace(wrong, correct)
    return text_lower


def _ensure_search_from_text(data: dict[str, Any], original_text: str) -> None:
    """Filet de sécurité : si l'IA n'a pas rempli 'search' mais que le texte
    utilisateur contient des noms de lieux connus (y compris déformés par la
    saisie vocale), on les injecte dans 'search'.
    """
    if data.get('search'):
        return

    corrected = _apply_voice_corrections(original_text)
    found: list[str] = []
    for loc in sorted(_KNOWN_LOCATIONS, key=len, reverse=True):
        if loc in corrected:
            found.append(loc)
            corrected = corrected.replace(loc, '')

    if found:
        data['search'] = ' '.join(found)
        logger.info('search_intent: injected fallback search=%r from user text', data['search'])
