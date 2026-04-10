"""Parsing JSON commun à tous les providers."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .exceptions import AIParseError

logger = logging.getLogger(__name__)


def parse_model_json(raw: str) -> dict[str, Any]:
    """Extrait un objet JSON depuis la sortie modèle (supprime fences ```json ... ```)."""
    if not raw or not str(raw).strip():
        raise AIParseError('Réponse vide.')
    text = str(raw).strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning('json decode error: %s — raw[:200]: %s', e, text[:200])
        raise AIParseError('Réponse JSON invalide.') from e
    if not isinstance(data, dict):
        raise AIParseError('Le JSON doit être un objet à la racine.')
    return data
