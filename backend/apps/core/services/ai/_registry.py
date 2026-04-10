"""
Registre des providers IA — Strategy Pattern léger.

Pour ajouter un nouveau provider :
1. Créer un fichier dans providers/
2. Implémenter une fonction qui respecte GenerateFn
3. Décorer avec @register_provider(name, priority)

Aucune modification de l'orchestrateur requise.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Protocol

logger = logging.getLogger(__name__)

GenerateFn = Callable[[str], str]


class AIProviderSpec(Protocol):
    """Contrat minimal qu'un provider doit respecter."""

    name: str

    def is_available(self) -> bool: ...
    def generate(self, prompt: str) -> str: ...


@dataclass(order=True)
class RegisteredProvider:
    """Provider enregistré avec sa priorité (plus bas = essayé en premier)."""
    priority: int
    name: str = field(compare=False)
    is_available: Callable[[], bool] = field(compare=False, repr=False)
    generate: GenerateFn = field(compare=False, repr=False)


_registry: list[RegisteredProvider] = []


def register_provider(
    name: str,
    priority: int,
    is_available: Callable[[], bool],
    generate: GenerateFn,
) -> None:
    """Enregistre un provider dans le registre global."""
    entry = RegisteredProvider(
        priority=priority,
        name=name,
        is_available=is_available,
        generate=generate,
    )
    _registry.append(entry)
    _registry.sort()
    logger.debug('ai registry: registered provider %s (priority=%d)', name, priority)


def get_providers() -> list[RegisteredProvider]:
    """Retourne les providers triés par priorité (plus bas en premier)."""
    return list(_registry)


def clear_registry() -> None:
    """Pour les tests uniquement."""
    _registry.clear()
