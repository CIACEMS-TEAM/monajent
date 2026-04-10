"""
Provider Gemini — google-genai SDK.
Priorité 90 (fallback) : 20 RPD free tier.
"""

from typing import Any

from django.conf import settings

from .._registry import register_provider


def _is_available() -> bool:
    return bool((getattr(settings, 'GEMINI_API_KEY', None) or '').strip())


def _generate(prompt: str) -> str:
    from google import genai
    from google.genai import types

    key = settings.GEMINI_API_KEY.strip()
    client = genai.Client(api_key=key)
    model = (getattr(settings, 'GEMINI_MODEL', None) or 'gemini-3-flash-preview').strip()

    kwargs: dict[str, Any] = {'model': model, 'contents': prompt}
    if 'gemini-3' in model.lower():
        kwargs['config'] = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level='low'),
        )

    response = client.models.generate_content(**kwargs)

    text = getattr(response, 'text', None)
    if text is None and getattr(response, 'candidates', None):
        parts = []
        for c in response.candidates or []:
            content = getattr(c, 'content', None)
            if content and getattr(content, 'parts', None):
                for p in content.parts:
                    if getattr(p, 'text', None):
                        parts.append(p.text)
        text = ''.join(parts) if parts else None
    if not text or not str(text).strip():
        raise ValueError('Réponse Gemini vide.')
    return str(text).strip()


register_provider(
    name='gemini',
    priority=90,
    is_available=_is_available,
    generate=_generate,
)
