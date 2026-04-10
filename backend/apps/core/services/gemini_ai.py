"""
Shim rétro-compatible — redirige vers le nouveau package apps.core.services.ai.

Tous les imports existants continuent de fonctionner :
  from apps.core.services import gemini_ai
  from apps.core.services.gemini_ai import GeminiParseError, parse_model_json
  gemini_ai.extract_listing_from_text(...)
"""

from apps.core.services.ai import (  # noqa: F401
    AIConfigurationError,
    AIParseError,
    AIProviderError,
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiParseError,
    extract_listing_from_text,
    parse_model_json,
    parse_search_intent,
)
