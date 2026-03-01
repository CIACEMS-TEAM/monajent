from __future__ import annotations

import re
from typing import Final

from django.conf import settings


_E164_REGEX: Final[re.Pattern[str]] = re.compile(r"^\+[1-9]\d{5,14}$")


def is_e164(value: str) -> bool:
    """
    Retourne True si value est au format E.164 (+CC...).
    """
    if not value:
        return False
    return bool(_E164_REGEX.match(value))


def normalize_to_e164(raw_phone: str) -> str:
    """
    Normalise un numéro 'raw_phone' vers E.164 en utilisant un indicatif par défaut.
    Politique simple, sans dépendances externes:
    - Si commence par '+', on garde '+' + chiffres uniquement.
    - Sinon, si commence par l'indicatif (ex: '225'), on préfixe '+'
    - Sinon, on PRÉSERVE les zéros initiaux et on préfixe l'indicatif par défaut (ex: '0544...' -> '+2250544...').
    """
    default_cc = getattr(settings, 'ORANGE_DEFAULT_COUNTRY_CODE', '+225')
    default_cc_digits = default_cc.lstrip('+')

    s = (raw_phone or '').strip()
    if not s:
        return ''

    if s.startswith('+'):
        digits = ''.join(ch for ch in s if ch.isdigit())
        normalized = f'+{digits}'
        return normalized

    digits_only = ''.join(ch for ch in s if ch.isdigit())
    if not digits_only:
        return ''

    # Si déjà commençant par l'indicatif (sans '+'), le garder tel quel avec '+'
    if digits_only.startswith(default_cc_digits):
        return f'+{digits_only}'

    # Conserver les zéros initiaux du numéro local pour compatibilité fournisseur (D7)
    normalized = f'+{default_cc_digits}{digits_only}'
    return normalized


