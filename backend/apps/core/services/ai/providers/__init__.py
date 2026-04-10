"""
Auto-discovery des providers IA.
Chaque module dans ce package s'auto-enregistre via register_provider() à l'import.
"""

import importlib
import logging
import pkgutil

logger = logging.getLogger(__name__)


def _auto_discover() -> None:
    """Importe tous les modules du package providers/ pour déclencher l'enregistrement."""
    package_path = __path__
    for _, module_name, _ in pkgutil.iter_modules(package_path):
        try:
            importlib.import_module(f'{__name__}.{module_name}')
        except Exception as e:
            logger.warning('ai: failed to load provider %s: %s', module_name, e)


_auto_discover()
