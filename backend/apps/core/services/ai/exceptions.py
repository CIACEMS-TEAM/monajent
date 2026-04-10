"""Exceptions partagées par tous les providers IA."""


class AIConfigurationError(Exception):
    """Aucun fournisseur IA configuré."""


class AIParseError(Exception):
    """Réponse modèle non JSON ou invalide."""


class AIProviderError(Exception):
    """Erreur réseau ou API du fournisseur."""


# Aliases rétro-compatibles (utilisés dans views/ai.py et tests)
GeminiConfigurationError = AIConfigurationError
GeminiParseError = AIParseError
GeminiAPIError = AIProviderError
